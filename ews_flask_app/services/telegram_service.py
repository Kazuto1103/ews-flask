"""
telegram_service.py
====================
Handles all Telegram Bot notifications for the EWS Banjir system.

Functions:
  send_telegram_message()    — Low-level raw message sender (MarkdownV2)
  send_flood_alert()         — Single-location alert with hourly breakdown
  send_full_broadcast()      — Full 4-location status summary report
  send_startup_notification()— System-online ping sent when Flask starts
  test_connection()          — Quick ping to verify bot credentials
"""

import requests
from datetime import datetime
from config import Config


# ─── MarkdownV2 Escaping ──────────────────────────────────────────────────────

def _e(text):
    """
    Escapes special characters for Telegram MarkdownV2.
    Required for: _ * [ ] ( ) ~ ` > # + - = | { } . !
    """
    special = r"\_*[]()~`>#+-=|{}.!"
    return "".join("\\" + c if c in special else c for c in str(text))


def _hr(length=32):
    """Returns an escaped horizontal rule of dashes."""
    return _e("─" * length)


# ─── Status Helpers ───────────────────────────────────────────────────────────

def _get_status_emoji(status_text):
    """Returns (dot_emoji, alert_emoji) for the given flood status."""
    upper = status_text.upper()
    if "BAHAYA" in upper:
        return "🔴", "🆘"
    elif "SIAGA" in upper:
        return "🟠", "🚨"
    elif "WASPADA" in upper:
        return "🟡", "⚠️"
    else:
        return "🟢", "✅"


def _get_recommendation(status_text):
    """Returns an actionable MarkdownV2-escaped recommendation string."""
    upper = status_text.upper()
    if "BAHAYA" in upper:
        return (
            "🆘 *DARURAT\\!* Potensi banjir bandang *SANGAT TINGGI*\\. "
            "Segera koordinasikan *evakuasi warga* di bantaran sungai\\. "
            "Hubungi BPBD dan aparat setempat\\!"
        )
    elif "SIAGA" in upper:
        return (
            "🚨 Siaga\\! Debit air mulai meningkat signifikan\\. "
            "Aktifkan posko tanggap darurat, evakuasi aset berharga ke tempat tinggi\\."
        )
    elif "WASPADA" in upper:
        return (
            "⚠️ Waspadai kenaikan debit air sungai\\. "
            "Siapkan logistik tanggap darurat, amankan dokumen penting, "
            "dan pantau kondisi setiap 30 menit\\."
        )
    else:
        return (
            "✅ Kondisi terpantau *aman* dan terkendali\\. "
            "Tetap lakukan pemantauan visual berkala\\."
        )


# ─── Low-Level Sender ─────────────────────────────────────────────────────────

def send_telegram_message(text, parse_mode="MarkdownV2", disable_notification=False):
    """
    Raw Telegram Bot API message sender.

    Returns:
        (bool, str): Success status and description message.
    """
    token   = Config.TELEGRAM_BOT_TOKEN
    chat_id = Config.TELEGRAM_CHAT_ID

    if not token or not chat_id:
        return False, "Telegram credentials not configured in .env (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID)"

    url     = "https://api.telegram.org/bot" + token + "/sendMessage"
    payload = {
        "chat_id":             chat_id,
        "text":                text,
        "parse_mode":          parse_mode,
        "disable_notification": disable_notification,
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        data     = response.json()
        if response.status_code == 200 and data.get("ok"):
            return True, "Message sent successfully."
        else:
            error_desc = data.get("description", "Unknown Telegram API Error")
            return False, "Telegram API Error: " + error_desc
    except requests.exceptions.ConnectionError:
        return False, "Network error: Could not reach Telegram API."
    except requests.exceptions.Timeout:
        return False, "Timeout: Telegram API did not respond within 10 seconds."
    except Exception as exc:
        return False, "Unexpected error: " + str(exc)


# ─── Alert Functions ──────────────────────────────────────────────────────────

def send_flood_alert(location, accumulation, status, hours=6, predictions=None):
    """
    Sends a detailed single-location flood early warning to Telegram.

    Args:
        location (str):     Station name e.g. 'Langkat_Hulu'
        accumulation (float): Accumulated rainfall in mm
        status (str):       Flood decision status text
        hours (int):        Accumulation window (3 or 6)
        predictions (list): Optional 12-element prediction vector for hourly breakdown

    Returns:
        (bool, str): Success flag and message.
    """
    now             = datetime.now().strftime("%d/%m/%Y %H:%M WIB")
    loc_display     = location.replace("_", " ")
    status_dot, alert_emoji = _get_status_emoji(status)
    recommendation  = _get_recommendation(status)

    # Pre-escape all dynamic values (no backslash inside f-string expressions)
    loc_esc    = _e(loc_display)
    accum_esc  = _e("{:.2f}".format(accumulation))
    hours_esc  = _e(str(hours))
    status_clean = status.replace("🟢 ", "").replace("🟡 ", "").replace("🟠 ", "").replace("🔴 ", "")
    status_esc = _e(status_clean)
    time_esc   = _e(now)
    hr         = _hr()

    # Optional hourly breakdown block
    hourly_section = ""
    if predictions and len(predictions) >= 6:
        rows = []
        for i, val in enumerate(predictions[:6], 1):
            bar_count = min(int(val / 5), 12)
            bar       = "█" * bar_count + "░" * (12 - bar_count)
            val_str   = "{:.1f}".format(val).rjust(6)
            rows.append("  Jam \\+" + str(i) + ": `" + _e(val_str) + " mm` " + _e(bar))
        hourly_section = "\n📊 *Proyeksi Hujan Per\\-Jam:*\n" + "\n".join(rows) + "\n"

    message = (
        alert_emoji + " *PERINGATAN DINI BANJIR EWS\\-SUMUT*\n"
        + hr + "\n"
        + "📍 *Stasiun Hulu:* " + loc_esc + "\n"
        + "🕐 *Waktu Laporan:* " + time_esc + "\n"
        + hr + "\n"
        + "☔ *Akumulasi " + hours_esc + " Jam:* `" + accum_esc + " mm`\n"
        + "📌 *Status Keputusan:* " + status_dot + " " + status_esc + "\n"
        + hourly_section
        + hr + "\n"
        + recommendation + "\n"
        + hr + "\n"
        + "🤖 _EWS\\-LSTM Hulu Sumatera Utara_"
    )

    return send_telegram_message(message)


def send_full_broadcast(all_predictions, flood_status):
    """
    Sends a full 4-location status summary report to Telegram.
    Called automatically on dashboard load or manually by the operator.

    Args:
        all_predictions (dict): {name: [12h prediction list]}
        flood_status (dict):    {name: {accum_3h, status_3h, accum_6h, status_6h, ...}}

    Returns:
        (bool, str): Success flag and message.
    """
    now    = datetime.now().strftime("%d/%m/%Y %H:%M WIB")
    hr     = _hr()

    display_names = {
        "Langkat_Hulu": "Langkat Hulu",
        "Medan_Hulu":   "Medan Hulu",
        "Sibolga_Hulu": "Sibolga Hulu",
        "Tapteng_Hulu": "Tapteng Hulu",
    }

    lines = [
        "🚨 *LAPORAN STATUS EWS BANJIR HULU SUMUT*",
        "🕐 " + _e(now),
        hr,
    ]

    for loc_key, loc_display in display_names.items():
        fs = flood_status.get(loc_key)
        if not fs:
            continue

        dot_3h, _ = _get_status_emoji(fs["status_3h"])
        dot_6h, _ = _get_status_emoji(fs["status_6h"])

        def _clean(s):
            return _e(s.replace("🟢 ", "").replace("🟡 ", "").replace("🟠 ", "").replace("🔴 ", ""))

        s3 = _clean(fs["status_3h"])
        s6 = _clean(fs["status_6h"])
        a3 = _e("{:.2f}".format(fs["accum_3h"]))
        a6 = _e("{:.2f}".format(fs["accum_6h"]))

        lines.append("📍 *" + _e(loc_display) + "*")
        lines.append("  3 Jam: `" + a3 + " mm` " + dot_3h + " " + s3)
        lines.append("  6 Jam: `" + a6 + " mm` " + dot_6h + " " + s6)
        lines.append(hr)

    lines.append("🤖 _EWS\\-LSTM Hulu Sumatera Utara_")

    return send_telegram_message("\n".join(lines))


def send_startup_notification():
    """
    Sends a system-online ping when the Flask application starts.
    Lets the operator know EWS monitoring is live.
    """
    now      = datetime.now().strftime("%d/%m/%Y %H:%M WIB")
    hr       = _hr()
    mode_str = "Mock \\(Data Sintetis\\)" if Config.MOCK_MODE else "Real \\(Data Aktual\\)"

    message = (
        "✅ *EWS BANJIR HULU SUMUT — SISTEM AKTIF*\n"
        + hr + "\n"
        + "🕐 *Waktu Mulai:* " + _e(now) + "\n"
        + "📡 *Mode:* " + mode_str + "\n"
        + "🛰 *Stasiun Dipantau:* 4 lokasi hulu SUMUT\n"
        + hr + "\n"
        + "Server EWS berhasil diaktifkan dan siap memantau kondisi curah hujan hulu\\.\n"
        + "🤖 _EWS\\-LSTM Hulu Sumatera Utara_"
    )
    return send_telegram_message(message)


def test_connection():
    """
    Sends a quick test ping to verify bot credentials are working.

    Returns:
        (bool, str): Success flag and message.
    """
    now = datetime.now().strftime("%d/%m/%Y %H:%M WIB")
    message = (
        "🔔 *Test Koneksi EWS Bot*\n"
        + _e(now) + "\n"
        + "Bot berfungsi normal\\! ✅"
    )
    return send_telegram_message(message)

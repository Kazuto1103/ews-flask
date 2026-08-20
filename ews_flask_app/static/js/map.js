document.addEventListener('DOMContentLoaded', function() {
    // 1. Initialize Map centered on North Sumatra
    const map = L.map('map').setView([2.6, 98.4], 8);
    
    // Add OpenStreetMap tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);

    // Layer Group for warning circles
    const circlesGroup = L.layerGroup().addTo(map);
    
    // Global data stores
    let locationsData = [];
    const slider = document.getElementById('timeSlider');
    const sliderValueDisplay = document.getElementById('sliderValue');

    // 2. Fetch predictions and coordinates from REST API
    fetch('/api/locations-data')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.locations) {
                locationsData = data.locations;
                
                // Adjust map zoom boundaries to cover all 4 points
                const points = locationsData.map(loc => [loc.lat, loc.lon]);
                const bounds = L.latLngBounds(points);
                map.fitBounds(bounds, { padding: [50, 50] });
                
                // Render initial hour projection (default: Hour 3)
                renderMapProjections(parseInt(slider.value));
            }
        })
        .catch(err => console.error("Gagal memuat koordinat EWS:", err));

    // 3. Render Warning Circles based on selected projection hour
    function renderMapProjections(hour) {
        // Clear old circles
        circlesGroup.clearLayers();
        
        locationsData.forEach(loc => {
            // Find prediction matching selected hour (0-indexed)
            const idx = hour - 1;
            const predInfo = loc.classifications[idx];
            
            const lat = loc.lat;
            const lon = loc.lon;
            const value = predInfo.value;
            const status = predInfo.status;
            const color = predInfo.color;
            const category = predInfo.kategori;
            const bmkgStatus = loc.bmkg_status;

            // Calculate scaled circle radius (in meters)
            // Baseline 15,000 meters, scaled by rainfall volume
            const calculatedRadius = Math.max(15000, value * 1500);
            
            // Build rich popup template matching original Folium popup
            const popupHtml = `
                <div style="font-family: 'Inter', sans-serif; width: 220px; line-height: 1.4;">
                    <h6 style="margin: 0 0 5px 0; font-weight: bold; color: #1e293b;">📍 Hulu ${loc.name}</h6>
                    <hr style="margin: 5px 0; border: 0; border-top: 1px solid #e2e8f0;">
                    <div style="font-size: 12px; margin-bottom: 8px;">
                        <span style="color: #64748b;">Projeksi:</span> <strong>Jam ke-${hour}</strong><br>
                        <span style="color: #64748b;">Curah Hujan:</span> <code>${value.toFixed(2)} mm/jam</code> (${category})
                    </div>
                    <div style="background-color: ${color}22; border-left: 4px solid ${color}; padding: 6px 10px; border-radius: 4px; font-weight: bold; font-size: 13px; color: ${color}; margin-bottom: 8px;">
                        Status: ${status}
                    </div>
                    <div style="font-size: 11px; color: #475569; background-color: #f1f5f9; padding: 6px; border-radius: 4px;">
                        📡 <b>Validasi BMKG:</b><br>${bmkgStatus}
                    </div>
                </div>
            `;
            
            // Draw Warning Circle
            const circle = L.circle([lat, lon], {
                color: color,
                weight: 2,
                fillColor: color,
                fillOpacity: 0.5,
                radius: calculatedRadius
            });
            
            circle.bindPopup(L.popup({ maxWidth: 260 }).setContent(popupHtml));
            
            circlesGroup.addLayer(circle);
        });
    }

    // 4. Bind Slider update events
    slider.addEventListener('input', function() {
        const val = this.value;
        sliderValueDisplay.innerText = `Jam ke-${val}`;
        renderMapProjections(parseInt(val));
    });
});

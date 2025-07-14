/**  LocationPicker.jsx  */
import { MapContainer, TileLayer, Marker, useMapEvents, useMap, GeoJSON } from 'react-leaflet';
import { GeoSearchControl, OpenStreetMapProvider } from 'leaflet-geosearch';
import L from 'leaflet';
import { useRef, useEffect, useState } from 'react';
import * as turf from '@turf/turf';




// default Icon → avoid marker bug 
const icon = new L.Icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

/**
 * A search bar component for a map that allows users to find locations by name.
 *
 * This component uses the OpenStreetMapProvider for geocoding and adds a search control
 * to the map. When a location is found, the map flies to the location, and the location
 * data is passed to the provided onResult callback function.
 *
 * @param {Function} onResult - Callback function that receives the location object
 * containing latitude (y), longitude (x), and other details when a search result is selected.
 */

function SearchBar({ onResult }) {
  const map = useMap();
  useEffect(() => {
    const provider = new OpenStreetMapProvider();
    const searchControl = new GeoSearchControl({
      provider,
      style: 'bar',
      marker: { icon },
      autoClose: true,
      showPopup: false,
      retainZoomLevel: false,
      searchLabel: 'Buscar dirección…',
    });

    map.addControl(searchControl);

    map.on('geosearch/showlocation', (e) => {
      const { y, x } = e.location;
      map.flyTo([y, x], map.getZoom(), { duration: 0.5 });
      onResult(e.location);
    });

    return () => map.removeControl(searchControl);
  }, [map, onResult]);
  return null;
}

/**
 * A map event handler that listens for clicks and passes the clicked location to the
 * provided onResult callback function.
 *
 * @param {Function} onResult - Callback function that receives the location object
 * containing latitude (y), longitude (x), and other details when the map is clicked.
 */
function ClickSelector({ onResult }) {
  useMapEvents({
    click: (e) =>
      onResult({
        x: e.latlng.lng,
        y: e.latlng.lat,
        label: `Lat: ${e.latlng.lat.toFixed(4)}, Lng: ${e.latlng.lng.toFixed(4)}`,
      }),
  });
  return null;
}
/**
 * LocationPicker component provides an interactive map for users to select a location.
 * It fetches and displays GeoJSON data representing the Andalucia region and ensures
 * that selected locations are within this region. Users can pick locations by clicking
 * on the map or using the search bar. The component manages and displays the selected
 * location and provides a confirm button to finalize the selection.
 *
 * Props:
 * @param {Array<number>} defaultPos - Default map center position as [latitude, longitude].
 * @param {Function} onConfirm - Callback function called with the selected location details
 *                               when the confirm button is clicked.
 */

export default function LocationPicker({ defaultPos = [37.3891, -5.9845], onConfirm }) {
  const mapRef = useRef(null);
  const [picked, setPicked] = useState(null);
  const [pickedData, setPickedData] = useState(null);
  const [geoJsonData, setGeoJsonData] = useState(null);

  useEffect(() => {
    fetch("/andalucia.geojson")
      .then((response) => response.json())
      .then((data) => setGeoJsonData(data))
      .catch((error) => console.error("Error loading GeoJSON:", error));
  }, []);

  /**
   * Handles location selection, updates the map position, and verifies if the
   * selected location is within the Andalucia region.
   *
   * @param {Object} loc - Location object with y (latitude), x (longitude), and
   *                       optional label properties.
   */
  const handlePick = (loc) => {
    const updateMapPosition = (position) => {
      setPicked(position);
      setPickedData({
        lat: position[0],
        lng: position[1],
        label: loc.label || `${position[0].toFixed(4)}, ${position[1].toFixed(4)}`
      });

      if (mapRef.current) {
        mapRef.current.flyTo(position, mapRef.current.getZoom(), { duration: 0.5 });
      }
    };

    const position = [loc.y, loc.x];


    if (!geoJsonData) {
      updateMapPosition(position);
      return;
    }

    // Verify if it's inside the polygon
    const point = turf.point([loc.x, loc.y]);
    const isInside = geoJsonData.features.some(feature =>
      turf.booleanPointInPolygon(point, feature.geometry)
    );

    if (isInside) {
      updateMapPosition(position);
    } else {
      // alert("Por favor, selecciona una ubicación dentro de Andalucía");
      setPicked(null);
      setPickedData(null);
    }
  };

  return (
    <div>
      <div className="relative">
        <MapContainer
          center={picked || defaultPos}
          zoom={7}
          whenCreated={(map) => (mapRef.current = map)}
          className="h-96 w-full rounded-xl"
          scrollWheelZoom
        >
          {geoJsonData && (
            <GeoJSON
              data={geoJsonData}
              style={{
                fillColor: '#6EE7B7',
                fillOpacity: 0.2,
                color: '#059669',
                weight: 2,
              }}
            />
          )}

          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          />

          {picked && <Marker position={picked} icon={icon} />}
          <SearchBar onResult={handlePick} />
          <ClickSelector onResult={handlePick} />
        </MapContainer>
      </div>

      {(
        <div className="flex justify-end mt-4">
          <button
            type="button"
            disabled={pickedData === null}
            className={`bg-blue-500 hover:bg-blue-600 text-white font-semibold py-2 px-4 mb-2 rounded-lg ${pickedData === null ? 'opacity-50 cursor-not-allowed' : 'hover:bg-indigo-200'
              }`}
            onClick={() => onConfirm(pickedData)}
          >
            Confirmar
          </button>

        </div>
      )}
    </div>
  );
}



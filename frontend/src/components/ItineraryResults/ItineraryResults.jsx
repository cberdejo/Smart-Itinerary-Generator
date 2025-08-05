import { useEffect, useRef, useState } from 'react';
import { Home, MapPin, Calendar, Building, ArrowLeft, Star, ChevronLeft, ChevronRight } from 'lucide-react';
import GenerateReport from './GenerateReport'
import AssetSection from './AssetSection'
import AssetItem from './AssetItem'
import polyline from '@mapbox/polyline';

import L from 'leaflet';
import 'leaflet/dist/leaflet.css';



/**
 * ItineraryResults component displays the itinerary results, including an interactive map
 * and detailed information about recommended towns. It uses Leaflet to render the map,
 * adds markers for each town, and allows users to click on a marker to view town details.
 * 
 * The component also provides an image carousel for each town and displays additional
 * information such as descriptions, history, real estate, and intangible assets.
 * 
 * Props:
 * @param {Object} results - Contains itinerary data including trip and towns information.
 * @param {Function} onReset - Callback function to reset the current view.
 */

export default function ItineraryResults({ results, onReset }) {
  const mapRef = useRef(null);
  const [selectedTown, setSelectedTown] = useState(null);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [showFullDescription, setShowFullDescription] = useState(false);
  const [showFullHistory, setShowFullHistory] = useState(false);
  const maxChars = 300;

  useEffect(() => {
    const map = mapRef.current;

    if (!map) {
      mapRef.current = L.map('map').setView([37.5443, -4.7278], 7);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
      }).addTo(mapRef.current);
    } else {
      map.eachLayer(layer => {
        if (layer instanceof L.Marker || layer instanceof L.Polyline) {
          map.removeLayer(layer);
        }
      });
    }

    const towns = results.towns;
    const trip = results.trip;
    const start = trip?.locations?.[0];

    const startingPoint = start ? [start.lat, start.lon] : [37.5443, -4.7278];

    if (start) {
      L.marker(startingPoint, {
        icon: L.icon({
          iconUrl: 'https://cdn-icons-png.flaticon.com/512/684/684908.png',
          iconSize: [30, 30],
          iconAnchor: [15, 30],
          popupAnchor: [0, -30],
        }),
        title: 'Punto de partida',
      }).addTo(mapRef.current).bindTooltip('Punto de partida', {
        direction: 'top',
        className: 'custom-tooltip'
      });
    }

    // add town markers
    towns.forEach(town => {
      const marker = L.marker([town.latitude, town.longitude], {
        icon: L.icon({
          iconUrl: 'https://cdn-icons-png.flaticon.com/512/2776/2776067.png',
          iconSize: [32, 32],
          iconAnchor: [16, 32],
          popupAnchor: [0, -32],
        }),
        title: town.municipality_name,
      }).addTo(mapRef.current);

      marker.bindTooltip(town.municipality_name, {
        direction: 'top',
        className: 'custom-tooltip',
      });

      marker.on('click', () => {
        setSelectedTown(town);
        setCurrentImageIndex(0);
        mapRef.current.setView([town.latitude, town.longitude], 12);
      });
    });

    const allLatLngs = [];

    trip.legs.forEach(leg => {
      if (leg.shape) {
        // Valhalla → precitionn 6
        const latlngs = polyline.decode(leg.shape, 6).map(([lat, lon]) => [lat, lon]);
        L.polyline(latlngs, {
          color: '#2563eb',          // tailwind "blue-600" aprox.
          weight: 4,
          opacity: 0.8,
        }).addTo(mapRef.current);
        allLatLngs.push(...latlngs);
      }
    });


    // Center the map on the starting point
    if (allLatLngs.length > 0) {
      mapRef.current.fitBounds(allLatLngs, { padding: [20, 20] });
    }

    mapRef.current.setView(startingPoint, 8);
  }, [results]);



  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <div className="flex flex-col gap-4">

            <h2 className="text-3xl font-bold text-gray-800">
              Municipios Recomendados
            </h2>

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">

              <p className="text-gray-600">
                Descubre {results.towns.length} destinos únicos para tu viaje
              </p>

              <div className="flex flex-col sm:flex-row gap-3 sm:justify-end">
                <button
                  onClick={onReset}
                  className="flex items-center gap-2 bg-gradient-to-r from-red-500 to-red-600 text-white px-6 py-3 rounded-xl hover:from-red-600 hover:to-red-700 transition-all duration-200 shadow-md hover:shadow-lg transform hover:-translate-y-0.5"
                >
                  <ArrowLeft className="w-4 h-4" />
                  Volver
                </button>

                <GenerateReport results={results} mapRef={mapRef} />
              </div>
            </div>
          </div>
        </div>


        <div className="grid grid-cols-1 lg:grid-cols-8 gap-4">
          {/* Map */}
          <div className="lg:col-span-6 bg-white rounded-xl shadow p-4">
            <div className="flex items-center gap-2 mb-3">
              <MapPin className="w-5 h-5 text-blue-600" />
              <h3 className="text-lg font-semibold text-gray-800">Mapa Interactivo</h3>
            </div>
            <div id="map" className="h-[600px]  rounded-lg shadow-inner" />
          </div>

          {/* Towns */}
          <div className="lg:col-span-2 bg-white rounded-xl shadow p-4">
            <div className="flex items-center gap-2 mb-3">
              <Star className="w-5 h-5 text-yellow-500" />
              <h3 className="text-lg font-semibold text-gray-800">Pueblos Destacados</h3>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-3">
              {results.towns.map((town) => (
                <div
                  key={town.municipality_ine}
                  className={`group cursor-pointer rounded-lg border overflow-hidden transition-all duration-300
            ${selectedTown?.municipality_ine === town.municipality_ine
                      ? 'bg-blue-50 border-blue-500 shadow-md -translate-y-0.5'
                      : 'bg-white border-gray-200 hover:border-blue-300 hover:shadow-md hover:-translate-y-0.5'}`}
                  onClick={() => {
                    setSelectedTown(town);
                    setCurrentImageIndex(0);
                    mapRef.current.setView([town.latitude, town.longitude], 12);
                  }}
                >
                  {/* Image */}
                  <div className="relative h-24 bg-gradient-to-br from-blue-400 to-blue-600">
                    {Array.isArray(town.images) && town.images[0]?.url ? (
                      <img
                        src={town.images[0].url}
                        alt={town.municipality_name}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <Home className="w-8 h-8 text-white opacity-80" />
                      </div>
                    )}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent" />
                  </div>

                  {/* Content */}
                  <div className="p-3">
                    <div className="flex items-start justify-between mb-1">
                      <h4 className="font-semibold text-gray-800 text-sm leading-tight line-clamp-2">
                        {town.municipality_name}
                      </h4>
                      {town.capital_city && (
                        <span className="ml-1 bg-yellow-100 text-yellow-800 text-[10px] px-2 py-0.5 rounded-full font-medium shrink-0">
                          Capital
                        </span>
                      )}
                    </div>

                    {/* Tags */}
                    <div className="space-y-1">
                      {town.real_estate_assets.length > 0 && (
                        <div className="flex flex-wrap gap-1 items-center">
                          <Building className="w-3 h-3 text-blue-600" />
                          {town.real_estate_assets.slice(0, 2).map((asset, i) => (
                            <span key={i} className="text-[10px] bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded-full">
                              {asset.name}
                            </span>
                          ))}
                          {town.real_estate_assets.length > 2 && (
                            <span className="text-[10px] bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded-full">
                              +{town.real_estate_assets.length - 2}
                            </span>
                          )}
                        </div>
                      )}

                      {town.intangible_assets.length > 0 && (
                        <div className="flex flex-wrap gap-1 items-center">
                          <Calendar className="w-3 h-3 text-green-600" />
                          {town.intangible_assets.slice(0, 2).map((asset, i) => (
                            <span key={i} className="text-[10px] bg-green-100 text-green-800 px-1.5 py-0.5 rounded-full">
                              {asset.name}
                            </span>
                          ))}
                          {town.intangible_assets.length > 2 && (
                            <span className="text-[10px] bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded-full">
                              +{town.intangible_assets.length - 2}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>


        {/* Selected Town Details */}
        {selectedTown && (
          <div className="bg-white rounded-2xl shadow-lg p-6 animate-in slide-in-from-bottom duration-600">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center">
                <MapPin className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-2xl font-bold text-gray-800">
                  {selectedTown.municipality_name}
                </h3>
                <p className="text-gray-600">
                  {selectedTown.capital_city ? 'Capital de provincia' : 'Municipio'}
                </p>
              </div>
            </div>
            {/* Image Carousel */}
            <div className=" relative w-128 aspect-ratio-16/9 overflow-hidden rounded-2xl  mx-auto">
              <img
                src={selectedTown.images[currentImageIndex].url}
                alt={selectedTown.images[currentImageIndex].alt || selectedTown.municipality_name}
                className="w-full h-full object-cover"
              />
              <div className="absolute" />

              {/* Navigation buttons */}
              {selectedTown.images.length > 1 && (
                <>
                  <button
                    onClick={() => setCurrentImageIndex(prev =>
                      prev === 0 ? selectedTown.images.length - 1 : prev - 1
                    )}
                    className="absolute left-2 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white text-gray-800 p-1 rounded-full shadow-md transition-all duration-200 hover:scale-110"
                  >
                    <ChevronLeft className="w-4 h-4 " />
                  </button>
                  <button
                    onClick={() => setCurrentImageIndex(prev =>
                      prev === selectedTown.images.length - 1 ? 0 : prev + 1
                    )}
                    className="absolute right-2 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white text-gray-800 p-1 rounded-full shadow-md transition-all duration-200 hover:scale-110"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </>

              )}
              {/* Image counter */}
              {selectedTown.images.length > 1 && (
                <div className="flex justify-between items-center mt-3">
                  <span className="text-sm text-gray-500">
                    {currentImageIndex + 1} de {selectedTown.images.length} imágenes
                  </span>
                  <div className="flex gap-2">
                    {selectedTown.images.slice(0, 4).map((image, index) => (
                      <button
                        key={index}
                        onClick={() => setCurrentImageIndex(index)}
                        className={`w-12 h-12 rounded-lg overflow-hidden border-2 transition-all duration-200 ${index === currentImageIndex
                          ? 'border-blue-500 scale-105'
                          : 'border-gray-200 hover:border-gray-300'
                          }`}
                      >
                        <img
                          src={image.url}
                          alt={image.alt || `${selectedTown.municipality_name} ${index + 1}`}
                          className="w-full h-full object-cover"
                        />
                      </button>
                    ))}
                    {selectedTown.images.length > 4 && (
                      <div className="w-12 h-12 rounded-lg  flex items-center justify-center">
                        <span className="text-xs text-gray-600 font-medium">
                          +{selectedTown.images.length - 4}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}

            </div>



            {/* Description */}
            {selectedTown.description && (
              <div className="mb-6">
                <h4 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  Descripción
                </h4>
                <p className="text-gray-700 leading-relaxed">
                  {showFullDescription || selectedTown.description.length <= maxChars
                    ? selectedTown.description
                    : `${selectedTown.description.slice(0, maxChars)}...`}
                </p>
                {selectedTown.description.length > maxChars && (
                  <button
                    className="mt-2 text-blue-600 hover:underline text-sm"
                    onClick={() => setShowFullDescription(!showFullDescription)}
                  >
                    {showFullDescription ? 'Ver menos' : 'Ver más'}
                  </button>
                )}
              </div>
            )}

            {/* History */}
            {selectedTown.history && selectedTown.history.trim() !== '' && (
              <div className="mb-6">
                <h4 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  Historia
                </h4>
                <p className="text-gray-600 leading-relaxed bg-gray-50 p-4 rounded-xl">
                  {showFullHistory || selectedTown.history.length <= maxChars
                    ? selectedTown.history
                    : `${selectedTown.history.slice(0, maxChars)}...`}
                </p>
                {selectedTown.history.length > maxChars && (
                  <button
                    className="mt-2 text-blue-600 hover:underline text-sm"
                    onClick={() => setShowFullHistory(!showFullHistory)}
                  >
                    {showFullHistory ? 'Ver menos' : 'Ver más'}
                  </button>
                )}
              </div>
            )}

            {/* Assets */}
            <div className="mb-6">
              <AssetSection
                title="Monumentos y Patrimonio"
                icon={<Building className="w-5 h-5 text-blue-600" />}
                bgClass={`bg-gradient-to-br from-blue-100 to-blue-50 rounded-xl p-5`}
              >
                {selectedTown.real_estate_assets.map((asset, idx) => (
                  <AssetItem
                    key={idx}
                    title={asset.name}
                    subtitle={asset.typologies?.map(t => t.den_tipologia).join(', ')}
                    dotColor="blue"
                    details={
                      <>
                        {asset.description && <p><strong>Descripción:</strong> {asset.description}</p>}
                        {asset.characterization && <p><strong>Caracterización:</strong> {asset.characterization}</p>}
                        {asset.typologies?.length > 0 && (
                          <>
                            {asset.typologies.some(t => t.den_tipologia && t.den_tipologia !== 'None') && (
                              <p>
                                <strong>Tipologías:</strong>{' '}
                                {asset.typologies
                                  .map(t => t.den_tipologia)
                                  .filter(t => t && t !== 'None')
                                  .join(', ')}
                              </p>
                            )}
                            {asset.typologies.some(t => t.den_etnia && t.den_etnia !== 'None') && (
                              <p>
                                <strong>Etnias:</strong>{' '}
                                {asset.typologies
                                  .map(t => t.den_etnia)
                                  .filter(t => t && t !== 'None')
                                  .join(', ')}
                              </p>
                            )}
                            {asset.typologies.some(t => t.periodos && t.periodos !== 'None') && (
                              <p>
                                <strong>Períodos:</strong>{' '}
                                {asset.typologies
                                  .map(t => t.periodos)
                                  .filter(t => t && t !== 'None')
                                  .join(', ')}
                              </p>
                            )}
                            {asset.typologies.some(t => t.denom_acti && t.denom_acti !== 'None') && (
                              <p>
                                <strong>Actividad:</strong>{' '}
                                {asset.typologies
                                  .map(t => t.denom_acti)
                                  .filter(t => t && t !== 'None')
                                  .join(', ')}
                              </p>
                            )}
                          </>
                        )}

                      </>
                    }
                  />
                ))}
              </AssetSection>
            </div>
            <div>
              <AssetSection
                className="mt-2"
                title="Festividades y Tradiciones"
                icon={<Calendar className="w-5 h-5 text-green-600" />}
                bgClass={`bg-gradient-to-br from-green-200 to-green-50 rounded-xl p-5`}


              >
                {selectedTown.intangible_assets.map((asset, idx) => (
                  <AssetItem
                    key={idx}
                    title={asset.name}
                    subtitle={asset.typology}
                    dotColor="green"
                    details={
                      <>
                        {asset.description && <p><strong>Descripción:</strong> {asset.description}</p>}
                        {asset.scope && <p><strong>Ámbito:</strong> {asset.scope}</p>}
                        {asset.typology && <p><strong>Tipología:</strong> {asset.typology}</p>}
                        {asset.date && <p><strong>Fecha:</strong> {asset.date}</p>}
                      </>
                    }
                  />
                ))}
              </AssetSection>
            </div>

          </div>
        )}
      </div>


    </div>
  );
}
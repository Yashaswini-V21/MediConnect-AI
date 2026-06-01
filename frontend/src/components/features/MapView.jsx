import React, { useState, useCallback } from 'react';
import { GoogleMap, LoadScript, Marker, InfoWindow, Circle } from '@react-google-maps/api';
import { MapPin, Phone, Navigation, Clock, Heart } from 'lucide-react';

const containerStyle = {
  width: '100%',
  height: '600px',
  borderRadius: '1.5rem',
};

const defaultCenter = {
  lat: 12.9716,
  lng: 77.5946, // Bangalore coordinates
};

const mapOptions = {
  zoomControl: true,
  streetViewControl: false,
  mapTypeControl: false,
  fullscreenControl: true,
  styles: [
    {
      featureType: 'poi.medical',
      elementType: 'all',
      stylers: [{ visibility: 'on' }]
    }
  ],
  disableDefaultUI: false,
  clickableIcons: true,
};

const MapView = ({ hospitals, userLocation }) => {
  const [selectedHospital, setSelectedHospital] = useState(null);
  const [map, setMap] = useState(null);

  const center = userLocation || defaultCenter;

  const handleMarkerClick = (hospital) => {
    setSelectedHospital(hospital);
    // Center map on selected hospital
    if (map) {
      map.panTo({ lat: hospital.latitude, lng: hospital.longitude });
    }
  };

  const getDirections = (hospital) => {
    const url = `https://www.google.com/maps/dir/?api=1&destination=${hospital.latitude},${hospital.longitude}`;
    window.open(url, '_blank');
  };

  const onLoad = useCallback((map) => {
    setMap(map);
  }, []);

  const onUnmount = useCallback(() => {
    setMap(null);
  }, []);

  return (
    <div className="relative">
      <LoadScript googleMapsApiKey={process.env.REACT_APP_GOOGLE_MAPS_API_KEY}>
        <GoogleMap
          mapContainerStyle={containerStyle}
          center={center}
          zoom={userLocation ? 13 : 12}
          options={mapOptions}
          onLoad={onLoad}
          onUnmount={onUnmount}
        >
          {/* User Location Marker with Pulse Animation */}
          {userLocation && (
            <>
              {/* User position circle */}
              <Circle
                center={userLocation}
                radius={500}
                options={{
                  strokeColor: '#3B82F6',
                  strokeOpacity: 0.8,
                  strokeWeight: 2,
                  fillColor: '#3B82F6',
                  fillOpacity: 0.2,
                }}
              />
              <Marker
                position={userLocation}
                icon={{
                  url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                    <svg width="40" height="40" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
                      <circle cx="20" cy="20" r="14" fill="#3B82F6" stroke="white" stroke-width="4" opacity="0.9"/>
                      <circle cx="20" cy="20" r="6" fill="white"/>
                    </svg>
                  `),
                  scaledSize: { width: 40, height: 40 },
                  anchor: { x: 20, y: 20 },
                }}
                zIndex={1000}
              />
            </>
          )}

          {/* Hospital Markers */}
          {hospitals?.map((hospital, idx) => (
            <Marker
              key={hospital.id}
              position={{ lat: hospital.latitude, lng: hospital.longitude }}
              onClick={() => handleMarkerClick(hospital)}
              animation={selectedHospital?.id === hospital.id ? window.google.maps.Animation.BOUNCE : null}
              icon={{
                url: hospital.emergency_available
                  ? 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                      <svg width="44" height="44" viewBox="0 0 44 44" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="22" cy="22" r="18" fill="#DC2626" stroke="white" stroke-width="3"/>
                        <rect x="19" y="10" width="6" height="24" fill="white" rx="1"/>
                        <rect x="10" y="19" width="24" height="6" fill="white" rx="1"/>
                        ${idx === 0 ? '<circle cx="22" cy="22" r="20" fill="none" stroke="#FBBF24" stroke-width="2" opacity="0.8"/>' : ''}
                      </svg>
                    `)
                  : 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                      <svg width="40" height="40" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="20" cy="20" r="16" fill="#10B981" stroke="white" stroke-width="3"/>
                        <rect x="17" y="9" width="6" height="22" fill="white" rx="1"/>
                        <rect x="9" y="17" width="22" height="6" fill="white" rx="1"/>
                      </svg>
                    `),
                scaledSize: hospital.emergency_available ? { width: 44, height: 44 } : { width: 40, height: 40 },
                anchor: hospital.emergency_available ? { x: 22, y: 22 } : { x: 20, y: 20 },
              }}
              zIndex={selectedHospital?.id === hospital.id ? 999 : (hospital.emergency_available ? 100 : 50)}
            />
          ))}

          {/* Enhanced Info Window */}
          {selectedHospital && (
            <InfoWindow
              position={{
                lat: selectedHospital.latitude,
                lng: selectedHospital.longitude,
              }}
              onCloseClick={() => setSelectedHospital(null)}
              options={{
                pixelOffset: new window.google.maps.Size(0, -20),
              }}
            >
              <div className="p-4 max-w-sm">
                <div className="mb-3">
                  <h3 className="font-bold text-xl mb-2 text-gray-900">{selectedHospital.name}</h3>
                  <div className="flex gap-2 mb-3">
                    {selectedHospital.emergency_available && (
                      <span className="inline-flex items-center gap-1 px-3 py-1 bg-red-100 text-red-700 text-xs font-bold rounded-full">
                        <Heart className="w-3 h-3" />
                        Emergency 24/7
                      </span>
                    )}
                    {selectedHospital.available_24_7 && (
                      <span className="inline-flex items-center gap-1 px-3 py-1 bg-green-100 text-green-700 text-xs font-bold rounded-full">
                        <Clock className="w-3 h-3" />
                        Open 24/7
                      </span>
                    )}
                  </div>
                </div>
                
                <div className="space-y-3 text-sm mb-4">
                  <div className="flex items-start gap-2">
                    <MapPin className="w-4 h-4 mt-1 flex-shrink-0 text-purple-600" />
                    <span className="text-gray-700">{selectedHospital.address}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Phone className="w-4 h-4 text-purple-600" />
                    <a
                      href={`tel:${selectedHospital.phone}`}
                      className="text-blue-600 hover:underline font-semibold"
                    >
                      {selectedHospital.phone}
                    </a>
                  </div>
                  {selectedHospital.distance && (
                    <div className="flex items-center gap-2">
                      <Navigation className="w-4 h-4 text-purple-600" />
                      <span className="text-gray-700 font-semibold">
                        {selectedHospital.distance.toFixed(1)} km away
                      </span>
                    </div>
                  )}
                  {selectedHospital.specialties && selectedHospital.specialties.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {selectedHospital.specialties.slice(0, 3).map((specialty, idx) => (
                        <span key={idx} className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full">
                          {specialty}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                
                <div className="flex gap-2">
                  <a
                    href={`tel:${selectedHospital.phone}`}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-red-600 text-white rounded-lg hover:bg-red-700 transition text-sm font-bold"
                  >
                    <Phone className="w-4 h-4" />
                    Call Now
                  </a>
                  <button
                    onClick={() => getDirections(selectedHospital)}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm font-bold"
                  >
                    <Navigation className="w-4 h-4" />
                    Navigate
                  </button>
                </div>
              </div>
            </InfoWindow>
          )}
        </GoogleMap>
      </LoadScript>
      
      {/* Map Legend */}
      <div className="absolute bottom-6 left-6 bg-white dark:bg-gray-800 rounded-xl shadow-xl p-4 border-2 border-purple-200 dark:border-purple-800">
        <h4 className="font-bold text-sm mb-3 text-gray-900 dark:text-white">Map Legend</h4>
        <div className="space-y-2 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-blue-600 border-2 border-white"></div>
            <span className="text-gray-700 dark:text-gray-300">Your Location</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-red-600 border-2 border-white"></div>
            <span className="text-gray-700 dark:text-gray-300">Emergency Available</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-green-600 border-2 border-white"></div>
            <span className="text-gray-700 dark:text-gray-300">General Hospital</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MapView;

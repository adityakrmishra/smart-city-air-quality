import React, { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import { ColorPalette } from '../utils/colors';
import { fetchSensorLocations } from '../api';

mapboxgl.accessToken = 'YOUR_MAPBOX_TOKEN';

const MapboxComponent = ({ 
  data, 
  onClick, 
  selectedSensor, 
  pollutionType,
  thresholds
}) => {
  const mapContainer = useRef(null);
  const [map, setMap] = useState(null);
  const [geojson, setGeojson] = useState({
    type: 'FeatureCollection',
    features: []
  });

  // Initialize map
  useEffect(() => {
    const initializeMap = async () => {
      const mapInstance = new mapboxgl.Map({
        container: mapContainer.current,
        style: 'mapbox://styles/mapbox/dark-v10',
        center: [12.4964, 41.9028], // Rome coordinates
        zoom: 11
      });

      mapInstance.on('load', async () => {
        const locations = await fetchSensorLocations();
        setGeojson({
          type: 'FeatureCollection',
          features: locations.map(sensor => ({
            type: 'Feature',
            geometry: {
              type: 'Point',
              coordinates: [sensor.lng, sensor.lat]
            },
            properties: {
              id: sensor.id,
              ...sensor
            }
          }))
        });

        // Add data sources and layers
        mapInstance.addSource('sensors', {
          type: 'geojson',
          data: geojson
        });

        mapInstance.addLayer({
          id: 'sensor-points',
          type: 'circle',
          source: 'sensors',
          paint: {
            'circle-radius': [
              'interpolate', ['linear'],
              ['get', pollutionType],
              thresholds[pollutionType].good, 8,
              thresholds[pollutionType].unhealthy, 24
            ],
            'circle-color': [
              'interpolate', ['linear'],
              ['get', pollutionType],
              thresholds[pollutionType].good, ColorPalette.good,
              thresholds[pollutionType].moderate, ColorPalette.moderate,
              thresholds[pollutionType].unhealthy, ColorPalette.unhealthy
            ],
            'circle-opacity': 0.8,
            'circle-stroke-width': 2,
            'circle-stroke-color': '#ffffff'
          }
        });

        // Add heatmap layer
        mapInstance.addLayer({
          id: 'pollution-heatmap',
          type: 'heatmap',
          source: 'sensors',
          maxzoom: 15,
          paint: {
            'heatmap-weight': [
              'interpolate', ['linear'],
              ['get', pollutionType],
              0, 0,
              thresholds[pollutionType].unhealthy, 1
            ],
            'heatmap-intensity': [
              'interpolate', ['linear'], ['zoom'],
              0, 1, 9, 3
            ],
            'heatmap-color': [
              'interpolate', ['linear'],
              ['heatmap-density'],
              0, 'rgba(33,102,172,0)',
              0.2, ColorPalette.good,
              0.4, ColorPalette.moderate,
              0.6, ColorPalette.unhealthy
            ],
            'heatmap-radius': [
              'interpolate', ['linear'], ['zoom'],
              0, 2, 9, 20
            ],
            'heatmap-opacity': 0.6
          }
        });
      });

      mapInstance.on('click', onClick);
      setMap(mapInstance);
    };

    if (!map) initializeMap();

    return () => map?.remove();
  }, []);

  // Update data visualization
  useEffect(() => {
    if (map && map.getSource('sensors')) {
      map.getSource('sensors').setData(geojson);
      map.setPaintProperty('sensor-points', 'circle-color', [
        'interpolate', ['linear'],
        ['get', pollutionType],
        thresholds[pollutionType].good, ColorPalette.good,
        thresholds[pollutionType].moderate, ColorPalette.moderate,
        thresholds[pollutionType].unhealthy, ColorPalette.unhealthy
      ]);
    }
  }, [geojson, pollutionType, thresholds]);

  // Highlight selected sensor
  useEffect(() => {
    if (map && selectedSensor) {
      map.flyTo({
        center: geojson.features.find(f => f.properties.id === selectedSensor)
          .geometry.coordinates,
        zoom: 14
      });
    }
  }, [selectedSensor]);

  return <div ref={mapContainer} className="map-container" />;
};

export default MapboxComponent;

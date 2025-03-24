import React, { useState, useEffect, useContext } from 'react';
import { SensorDataContext } from './contexts/SensorDataContext';
import MapboxComponent from './components/MapboxComponent';
import ARControls from './components/ARControls';
import DataPanel from './components/DataPanel';
import Legend from './components/Legend';
import TimeControls from './components/TimeControls';
import { WebsocketProvider } from './contexts/WebsocketContext';
import { ColorPalette } from './utils/colors';
import { processHistoricalData } from './utils/dataProcessing';

const App = () => {
  const { realtimeData, historicalData } = useContext(SensorDataContext);
  const [selectedSensor, setSelectedSensor] = useState(null);
  const [timeRange, setTimeRange] = useState('24h');
  const [pollutionType, setPollutionType] = useState('pm25');
  const [arMode, setArMode] = useState(false);
  const [thresholds, setThresholds] = useState({
    pm25: { good: 12, moderate: 35, unhealthy: 55 },
    pm10: { good: 54, moderate: 154, unhealthy: 254 }
  });

  // Process data for visualization
  const processedData = processHistoricalData(
    historicalData, 
    timeRange, 
    pollutionType
  );

  // WebSocket message handler
  const handleNewData = (data) => {
    console.log('New real-time data:', data);
  };

  // Map click handler
  const handleMapClick = (e) => {
    const features = e.target.queryRenderedFeatures(e.point, {
      layers: ['sensor-points']
    });
    setSelectedSensor(features[0]?.properties?.id || null);
  };

  // Toggle AR mode
  const toggleAR = () => {
    setArMode(!arMode);
    if(!arMode) document.body.requestFullscreen();
  };

  return (
    <WebsocketProvider onMessage={handleNewData}>
      <div className="app-container">
        {!arMode ? (
          <>
            <div className="map-container">
              <MapboxComponent 
                data={processedData}
                onClick={handleMapClick}
                selectedSensor={selectedSensor}
                pollutionType={pollutionType}
                thresholds={thresholds}
              />
              <div className="controls-overlay">
                <TimeControls 
                  timeRange={timeRange}
                  onChange={setTimeRange}
                />
                <ARControls 
                  arMode={arMode}
                  onToggle={toggleAR}
                />
              </div>
              <Legend 
                pollutionType={pollutionType}
                thresholds={thresholds}
                colors={ColorPalette}
              />
            </div>
            <DataPanel 
              sensor={selectedSensor}
              realtimeData={realtimeData}
              historicalData={historicalData}
              pollutionType={pollutionType}
              onPollutionChange={setPollutionType}
            />
          </>
        ) : (
          <iframe 
            src="/ar_overlays/ar_pollution.html"
            className="ar-frame"
            title="AR Pollution Visualization"
          />
        )}
      </div>
    </WebsocketProvider>
  );
};

export default App;

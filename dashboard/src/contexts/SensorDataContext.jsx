import React, { createContext, useContext, useState, useEffect } from 'react';
import { fetchHistoricalData, fetchRealtimeData } from '../api';

const SensorDataContext = createContext();

export const SensorDataProvider = ({ children }) => {
  const [realtimeData, setRealtimeData] = useState([]);
  const [historicalData, setHistoricalData] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const updateData = async (timeRange = '24h') => {
    try {
      setLoading(true);
      const [realtime, historical] = await Promise.all([
        fetchRealtimeData(),
        fetchHistoricalData(timeRange)
      ]);
      setRealtimeData(realtime);
      setHistoricalData(historical);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    updateData();
    const interval = setInterval(updateData, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <SensorDataContext.Provider 
      value={{ realtimeData, historicalData, loading, error, updateData }}
    >
      {children}
    </SensorDataContext.Provider>
  );
};

export const useSensorData = () => useContext(SensorDataContext);

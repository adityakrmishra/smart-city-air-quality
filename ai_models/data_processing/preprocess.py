"""
Air Quality Data Preprocessing Pipeline
- Handles missing values
- Creates temporal features
- Normalizes/encodes data
- Generates sequences for ML models
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import train_test_split
from datetime import datetime

class AirQualityPreprocessor:
    def __init__(self, config: dict = None):
        self.config = config or {
            'time_features': True,
            'cyclical_encoding': True,
            'lag_features': 3,
            'test_size': 0.2,
            'random_state': 42
        }
        self.scalers = {}
        
    def load_data(self, file_path: str) -> pd.DataFrame:
        """Load raw CSV data with datetime parsing"""
        df = pd.read_csv(
            file_path,
            parse_dates=['timestamp'],
            infer_datetime_format=True
        )
        df.sort_values('timestamp', inplace=True)
        return df

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values and outliers"""
        # Forward fill missing temporal data
        df = df.ffill(limit=2).bfill(limit=1)
        
        # Remove remaining NaNs
        df.dropna(inplace=True)
        
        # Clip outliers using IQR
        for col in ['pm25', 'pm10', 'wind_speed']:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            df[col] = np.clip(df[col], q1 - 1.5*iqr, q3 + 1.5*iqr)
            
        return df

    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create temporal and meteorological features"""
        # Time-based features
        if self.config['time_features']:
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            df['month'] = df['timestamp'].dt.month
            
        # Cyclical encoding for wind direction
        if self.config['cyclical_encoding']:
            df['wind_dir_sin'] = np.sin(2 * np.pi * df['wind_direction']/360)
            df['wind_dir_cos'] = np.cos(2 * np.pi * df['wind_direction']/360)
            
        # Lag features for pollution levels
        if self.config['lag_features'] > 0:
            for lag in range(1, self.config['lag_features'] + 1):
                df[f'pm25_lag_{lag}'] = df['pm25'].shift(lag)
                df[f'pm10_lag_{lag}'] = df['pm10'].shift(lag)
                
        # Rolling statistics
        df['pm25_rolling_3h'] = df['pm25'].rolling(window=3).mean()
        df['wind_speed_rolling_3h'] = df['wind_speed'].rolling(window=3).mean()
        
        # Drop original wind direction
        df.drop('wind_direction', axis=1, inplace=True)
        
        return df.dropna()  # Remove rows with NaN from shifts

    def scale_features(self, df: pd.DataFrame) -> (pd.DataFrame, dict):
        """Normalize features using robust scaling"""
        features_to_scale = [
            'wind_speed', 'temperature', 'humidity',
            'pm25', 'pm10', 'pm25_rolling_3h'
        ]
        
        scalers = {}
        scaled_df = df.copy()
        
        for col in features_to_scale:
            scaler = RobustScaler()
            scaled_df[col] = scaler.fit_transform(scaled_df[[col]].values)
            scalers[col] = scaler
            
        self.scalers = scalers
        return scaled_df, scalers

    def train_test_split(self, df: pd.DataFrame) -> tuple:
        """Time-aware split of data"""
        split_idx = int(len(df) * (1 - self.config['test_size']))
        train = df.iloc[:split_idx]
        test = df.iloc[split_idx:]
        return train, test

    def full_pipeline(self, file_path: str) -> tuple:
        """Execute complete preprocessing pipeline"""
        df = self.load_data(file_path)
        df = self.clean_data(df)
        df = self.engineer_features(df)
        df, scalers = self.scale_features(df)
        train, test = self.train_test_split(df)
        return train, test, scalers

if __name__ == "__main__":
    # Example usage
    preprocessor = AirQualityPreprocessor()
    train_data, test_data, scalers = preprocessor.full_pipeline("wind_patterns.csv")
    
    print("Training Data Shape:", train_data.shape)
    print("Test Data Shape:", test_data.shape)
    print("Sample Training Features:\n", train_data.iloc[0])

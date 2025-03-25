import pytest
import numpy as np
from ai_models.lstm_forecasting.lstm_training import PollutionLSTM, create_sequences

def test_lstm_model_forward_pass():
    model = PollutionLSTM(input_size=6)
    dummy_input = torch.randn(32, 10, 6)  # (batch, seq, features)
    output = model(dummy_input)
    assert output.shape == (32, 1)

def test_sequence_generation():
    data = np.random.rand(100, 6)
    sequences = create_sequences(data, window=10)
    assert len(sequences) == 90
    seq, label = sequences[0]
    assert seq.shape == (10, 6)
    assert label.shape == (6,)

def test_prophet_forecast():
    from ai_models.lstm_forecasting.prophet_model import PollutionProphet
    prophet = PollutionProphet()
    train_data = pd.DataFrame({
        'timestamp': pd.date_range(start='2023-01-01', periods=100, freq='H'),
        'pm25': np.random.normal(35, 5, 100),
        'wind_speed': np.random.uniform(0, 10, 100)
    })
    prophet.fit(train_data)
    forecast = prophet.predict(horizon=24)
    assert len(forecast) == 24
    assert 'yhat' in forecast.columns

from fbprophet import Prophet
import pandas as pd

class PollutionProphet:
    """Wrapper for Facebook Prophet forecasting"""
    def __init__(self, growth='logistic', changepoints=10):
        self.model = Prophet(
            growth=growth,
            changepoint_prior_scale=0.3,
            seasonality_mode='multiplicative'
        )
        self.model.add_seasonality(name='hourly', period=1, fourier_order=3)
        
    def fit(self, df, regressors=['wind_speed', 'temperature']):
        for reg in regressors:
            self.model.add_regressor(reg)
        train_df = df.rename(columns={'timestamp': 'ds', 'pm25': 'y'})
        self.model.fit(train_df[['ds', 'y'] + regressors])
        
    def predict(self, horizon=24, freq='H'):
        future = self.model.make_future_dataframe(
            periods=horizon, 
            freq=freq,
            include_history=False
        )
        return self.model.predict(future)

    def cross_validate(self, initial='5 days', period='1 day', horizon='1 day'):
        return cross_validation(
            self.model,
            initial=initial,
            period=period,
            horizon=horizon
        )

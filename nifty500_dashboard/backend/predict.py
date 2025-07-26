import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from datetime import timedelta

def get_prediction(symbol, degree=3):
    df = pd.read_csv(f'backend/data/{symbol}.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    df['Days'] = (df['Date'] - df['Date'].min()).dt.days

    X = df[['Days']]
    y = df['Close']

    poly = PolynomialFeatures(degree=degree)
    X_poly = poly.fit_transform(X)
    model = LinearRegression().fit(X_poly, y)

    last_day = df['Days'].iloc[-1]
    future_days = pd.DataFrame({'Days': [last_day + i for i in range(1, 11)]})  # Fix for warning
    future_days_poly = poly.transform(future_days)
    predictions = model.predict(future_days_poly)

    future_dates = [df['Date'].iloc[-1] + timedelta(days=i) for i in range(1, 11)]
    return pd.DataFrame({'Date': future_dates, 'Predicted': predictions})

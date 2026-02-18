import requests
import pandas as pd
from datetime import datetime

LAT_MIN, LAT_MAX = 40.70, 40.80
LON_MIN, LON_MAX = -74.25, -74.15

url = "https://api.open-meteo.com/v1/forecast"

params = {
    "latitude": (LAT_MIN + LAT_MAX) / 2,
    "longitude": (LON_MIN + LON_MAX) / 2,
    "hourly": "precipitation",
    "timezone": "UTC"
}

r = requests.get(url, params=params)
data = r.json()

df = pd.DataFrame({
    "time": data["hourly"]["time"],
    "precip_mm": data["hourly"]["precipitation"]
})

df["time"] = pd.to_datetime(df["time"])
df.to_csv(r"C:\Users\abtah\PycharmProjects\FlashFlooding\data_dynamic_raw\rainfall\rain_hourly.csv", index=False)

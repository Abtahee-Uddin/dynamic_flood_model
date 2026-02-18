import pandas as pd
import numpy as np
import rasterio
import os
from rasterio.transform import from_bounds
folder = r"C:\Users\abtah\PycharmProjects\FlashFlooding\data_dynamic_raw\rainfall"

for f in os.listdir(folder):
    if f.endswith(".tif"):
        os.remove(os.path.join(folder, f))

df = pd.read_csv(r"C:\Users\abtah\PycharmProjects\FlashFlooding\data_dynamic_raw\rainfall\rain_hourly.csv")
df["time"] = pd.to_datetime(df["time"])
STATIC_FV = r"C:\Users\abtah\PycharmProjects\FlashFlooding\data_static\static_flood_vulnerability.tif"

with rasterio.open(STATIC_FV) as ref:
    profile = ref.profile
    bounds = ref.bounds
    width = ref.width
    height = ref.height

for _, row in df.iterrows():
    rain = row["precip_mm"]
    timestamp = row["time"].strftime("%Y%m%d_%H")

    data = np.full((height, width), rain, dtype="float32")

    profile.update(
        dtype="float32",
        count=1,
        compress="lzw"
    )

    out_path = fr"C:\Users\abtah\PycharmProjects\FlashFlooding\data_dynamic_raw\rainfall\rain_{timestamp}.tif"

    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(data, 1)

    print(f"Saved {out_path}")

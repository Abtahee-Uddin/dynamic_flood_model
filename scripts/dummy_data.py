import os
import rasterio
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE_DIR)

STATIC = "data_static/static_fv_10m.tif"

os.makedirs("data_dynamic_raw/rainfall", exist_ok=True)
os.makedirs("data_dynamic_raw/soil", exist_ok=True)

with rasterio.open(STATIC) as src:
    shape = src.shape
    meta = src.meta.copy()

meta.update(dtype=rasterio.float32)

storm = {
    "12": 20.0,
    "13": 30.0,
    "14": 40.0
}

for hour, value in storm.items():
    rain = np.full(shape, value)
    path = f"data_dynamic_raw/rainfall/rain_20260206_{hour}.tif"

    with rasterio.open(path, "w", **meta) as dst:
        dst.write(rain.astype(np.float32), 1)

# Soil constant
wet = np.full(shape, 0.6)

with rasterio.open("data_dynamic_raw/soil/wf_20260206.tif", "w", **meta) as dst:
    dst.write(wet.astype(np.float32), 1)

print("Dummy rainfall and soil created.")

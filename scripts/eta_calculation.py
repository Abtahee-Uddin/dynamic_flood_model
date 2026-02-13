import os
import rasterio
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE_DIR)

dynamic_files = [
    ("12", "data_dynamic_processed/dynamic_risk/dyn_12.tif"),
    ("13", "data_dynamic_processed/dynamic_risk/dyn_13.tif"),
    ("14", "data_dynamic_processed/dynamic_risk/dyn_14.tif"),
]

THRESHOLD = 0.4

with rasterio.open(dynamic_files[0][1]) as src:
    shape = src.shape
    meta = src.meta.copy()

eta_map = np.zeros(shape)

for hour, file in dynamic_files:
    with rasterio.open(file) as src:
        data = src.read(1)

    mask = (data >= THRESHOLD) & (eta_map == 0)
    eta_map[mask] = int(hour)

meta.update(dtype=rasterio.float32)

with rasterio.open("data_dynamic_processed/eta_map.tif", "w", **meta) as dst:
    dst.write(eta_map.astype(np.float32), 1)

print("ETA map created.")

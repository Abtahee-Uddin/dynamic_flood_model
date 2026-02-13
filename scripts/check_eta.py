import os
import rasterio
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE_DIR)

with rasterio.open("data_dynamic_processed/eta_map.tif") as src:
    data = src.read(1)

print("Unique ETA values:", np.unique(data))

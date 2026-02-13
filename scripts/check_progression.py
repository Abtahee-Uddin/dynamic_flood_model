import os
import rasterio
import numpy as np

# Move to project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE_DIR)

files = [
    "data_dynamic_processed/dynamic_risk/dyn_12.tif",
    "data_dynamic_processed/dynamic_risk/dyn_13.tif",
    "data_dynamic_processed/dynamic_risk/dyn_14.tif"
]

for f in files:
    with rasterio.open(f) as src:
        data = src.read(1)
    print(f, "Max:", np.nanmax(data))

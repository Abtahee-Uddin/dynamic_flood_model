import rasterio
import numpy as np
import os

# #Check original static vulnerability
# with rasterio.open("data_static/static_fv.tif") as src:
#     data = src.read(1)
#     print("CRS:", src.crs)
#     print("Shape:", src.shape)
#     print("Bands:", src.count)
#     print("Resolution:", src.res )

#     # data = src.read(1)
#     # data = np.where(data < -1e30, np.nan, data)

# print("raw min:", np.min(data))
# print("raw mac:", np.max(data))



#Check resampled static vulnerability

# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# os.chdir(BASE_DIR)

# with rasterio.open("data_static/static_fv_10m.tif") as src:
#     data = src.read(1)

#     print("CRS:", src.crs)
#     print("Shape:", src.shape)
#     print("Resolution:", src.res)

#     print("Raw Min:", np.min(data))
#     print("Raw Max:", np.max(data))

#     clean = np.where(data < -1e30, np.nan, data)

#     print("Clean Min:", np.nanmin(clean))
#     print("Clean Max:", np.nanmax(clean))

#dynamic core values check
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

    print(f)
    print("  Min:", np.nanmin(data))
    print("  Max:", np.nanmax(data))
    print("--------------------------------")

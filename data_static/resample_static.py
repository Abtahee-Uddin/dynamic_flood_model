import rasterio
from rasterio.enums import Resampling
from rasterio.warp import calculate_default_transform, reproject

INPUT = "data_static/static_fv.tif"
OUTPUT = "data_static/static_fv_10m.tif"

TARGET_RES = 10  # meters

with rasterio.open(INPUT) as src:
    transform, width, height = calculate_default_transform(
        src.crs,
        src.crs,
        src.width,
        src.height,
        *src.bounds,
        resolution=TARGET_RES
    )

    meta = src.meta.copy()
    meta.update({
        "height": height,
        "width": width,
        "transform": transform
    })

    with rasterio.open(OUTPUT, "w", **meta) as dst:
        reproject(
            source=rasterio.band(src, 1),
            destination=rasterio.band(dst, 1),
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=transform,
            dst_crs=src.crs,
            resampling=Resampling.bilinear
        )

print("Resampling completed correctly.")

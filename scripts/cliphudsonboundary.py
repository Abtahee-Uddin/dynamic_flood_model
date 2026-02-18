import geopandas as gpd
import rasterio
from rasterio.mask import mask
from rasterio.features import geometry_mask
import numpy as np
from pathlib import Path
import json


# CONFIGURATION

# Input directory (output from automated_ee_download.py)
INPUT_DIR = Path("wetness_factor_rasters")

# Output directory (clipped rasters)
OUTPUT_DIR = Path("wetness_factor_clipped")
OUTPUT_DIR.mkdir(exist_ok=True)

# Hudson County boundary file
BOUNDARY_FILE = "hudson_county.gpkg"

# CLIP RASTERS

def clip_rasters_to_boundary():
    """Clip all wetness factor rasters to Hudson County boundary"""
    
   
    print("CLIPPING RASTERS TO HUDSON COUNTY BOUNDARY")
   
    
    # Load Hudson County boundary
    print(f"\nLoading boundary: {BOUNDARY_FILE}")
    
    if not Path(BOUNDARY_FILE).exists():
        print(f"ERROR: File not found: {BOUNDARY_FILE}")
        print("   Make sure hudson_county.gpkg is in the current directory")
        return []
    
    gdf = gpd.read_file(BOUNDARY_FILE)
    
    print(f"   CRS: {gdf.crs}")
    print(f"   Features: {len(gdf)}")
    print(f"   Bounds: {gdf.total_bounds}")
    
    # Get all wetness factor rasters
    input_files = sorted(INPUT_DIR.glob("wf_*.tif"))
    
    if not input_files:
        print(f"\nERROR: No wetness factor rasters found in {INPUT_DIR}")
        print("   Run automated_ee_download.py first!")
        return []
    
    print(f"\nFound {len(input_files)} rasters to clip")
    
    # Reproject boundary to match raster CRS
    with rasterio.open(input_files[0]) as src:
        raster_crs = src.crs
        print(f"\nTarget CRS: {raster_crs}")
    
    if gdf.crs != raster_crs:
        print(f"   Reprojecting boundary from {gdf.crs} to {raster_crs}...")
        gdf = gdf.to_crs(raster_crs)
    
    # Get geometry for clipping
    geometries = [json.loads(gdf.to_json())['features'][0]['geometry']]
    
    # Clip each raster
    output_files = []
    
    print("\nClipping rasters...")
    
    for i, input_file in enumerate(input_files):
        print(f"\n   [{i+1}/{len(input_files)}] {input_file.name}")
        
        try:
            with rasterio.open(input_file) as src:
                # Clip raster to boundary
                out_image, out_transform = mask(
                    src,
                    geometries,
                    crop=True,
                    nodata=0,
                    all_touched=True
                )
                
                # Update metadata
                out_meta = src.meta.copy()
                out_meta.update({
                    "driver": "GTiff",
                    "height": out_image.shape[1],
                    "width": out_image.shape[2],
                    "transform": out_transform,
                    "nodata": 0,
                    "compress": "lzw"
                })
                
                # Output file
                output_file = OUTPUT_DIR / input_file.name
                
                # Write clipped raster
                with rasterio.open(output_file, "w", **out_meta) as dest:
                    dest.write(out_image)
                
                # Stats
                valid_data = out_image[0][out_image[0] != 0]
                
                if len(valid_data) > 0:
                    print(f"      SUCCESS: Clipped size: {out_image.shape[2]} x {out_image.shape[1]}")
                    print(f"         Range: {valid_data.min():.3f} - {valid_data.max():.3f}")
                    output_files.append(output_file)
                else:
                    print(f"      WARNING: No valid data after clipping")
        
        except Exception as e:
            print(f"      ERROR: Failed: {e}")
            continue
    
    return output_files

# VERIFY

def verify_clipped_rasters(files):
    """Verify clipped rasters"""
    
  
    print("VERIFICATION")
   
    
    # Load boundary for comparison
    gdf = gpd.read_file(BOUNDARY_FILE)
    
    # Check first and last file
    for idx in [0, -1]:
        if idx < len(files):
            print(f"\nCHECK: {files[idx].name}")
            
            with rasterio.open(files[idx]) as src:
                print(f"   CRS: {src.crs}")
                print(f"   Size: {src.width} x {src.height}")
                print(f"   Bounds: {src.bounds}")
                
                data = src.read(1)
                valid = data[data != 0]
                
                if len(valid) > 0:
                    print(f"   Values: {valid.min():.3f} - {valid.max():.3f}")
                    print(f"   Valid pixels: {len(valid):,}")
                else:
                    print(f"   WARNING: No valid data!")

# COMPARE BEFORE/AFTER

def show_comparison():
    """Show before/after statistics"""
    
  
    print("BEFORE vs AFTER COMPARISON")
    
    
    input_files = sorted(INPUT_DIR.glob("wf_*.tif"))
    output_files = sorted(OUTPUT_DIR.glob("wf_*.tif"))
    
    if input_files and output_files:
        # Compare first file
        print(f"\nSample file: {input_files[0].name}")
        
        with rasterio.open(input_files[0]) as src_before:
            data_before = src_before.read(1)
            valid_before = data_before[data_before != 0]
            
            print(f"\n   BEFORE (Rectangle):")
            print(f"      Size: {src_before.width} x {src_before.height}")
            print(f"      Valid pixels: {len(valid_before):,}")
        
        with rasterio.open(output_files[0]) as src_after:
            data_after = src_after.read(1)
            valid_after = data_after[data_after != 0]
            
            print(f"\n   AFTER (Clipped to Hudson County):")
            print(f"      Size: {src_after.width} x {src_after.height}")
            print(f"      Valid pixels: {len(valid_after):,}")
            
            # Calculate reduction
            reduction = (1 - len(valid_after) / len(valid_before)) * 100
            print(f"\n   Pixels removed: {reduction:.1f}%")


# ======
# MAIN
# ======

def main():
    """Main execution"""
    
    try:
        # Clip rasters
        output_files = clip_rasters_to_boundary()
        
        if not output_files:
            print("\nERROR: No files created")
            return
        
        # Verify
        verify_clipped_rasters(output_files)
        
        # Show comparison
        show_comparison()
        
        # Summary
      
        print("SUCCESS - RASTERS CLIPPED TO BOUNDARY!")      
        print(f"\nInput: {INPUT_DIR}")
        print(f"Output: {OUTPUT_DIR}")
        print(f"Files processed: {len(output_files)}")
        
       
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

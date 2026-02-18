import ee
import requests
import numpy as np
import rasterio
from rasterio.transform import from_bounds
from rasterio.warp import reproject, Resampling, calculate_default_transform
from pathlib import Path
from datetime import datetime, timedelta
import time


# CONFIGURATION


# Hudson County bounding box
HUDSON_BBOX = {
    'west': -74.17,
    'south': 40.64,
    'east': -73.99,
    'north': 40.85
}

# Date to download (60 days ago)
TARGET_DATE = datetime.now() - timedelta(days=7)

# Output directory
OUTPUT_DIR = Path("wetness_factor_rasters")
OUTPUT_DIR.mkdir(exist_ok=True)

# Target CRS
TARGET_CRS = "EPSG:26918"  # NAD83 UTM Zone 18N

# =
# INITIALIZE
# =

def initialize_ee():
    """Initialize Earth Engine with project"""
    
    print("=" * 70)
    print("AUTOMATED EARTH ENGINE DOWNLOAD")
    print("=" * 70)
    
    print("\n🔧 Initializing Earth Engine...")
    
    # Try different initialization methods
    methods = [
        ('earth-engine-hudson', 'Your registered project'),
        ('ee-default', 'Default project'),
    ]
    
    for project_id, description in methods:
        try:
            ee.Initialize(project=project_id)
            print(f" Connected using: {description}")
            return True
        except:
            continue
    
    # If all fail, ask user
    print("\n  Need project ID")
    project = input("Enter your Earth Engine project ID: ").strip()
    
    if project:
        try:
            ee.Initialize(project=project)
            print(f" Connected!")
            return True
        except Exception as e:
            print(f" Failed: {e}")
            return False
    
    return False

# =
# DOWNLOAD DIRECTLY
# =

def download_and_process():
    """Download soil moisture and process in one go"""
    
    print(f"\n Date: {TARGET_DATE.date()}")
    print(f" Area: Hudson County, NJ")
    print(f" Target CRS: {TARGET_CRS}")
    
    # Define area
    aoi = ee.Geometry.Rectangle([
        HUDSON_BBOX['west'],
        HUDSON_BBOX['south'],
        HUDSON_BBOX['east'],
        HUDSON_BBOX['north']
    ])
    
    # Load dataset
    print("\n Loading ERA5-Land dataset...")
    dataset = ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY')
    
    # Filter
    start_date = TARGET_DATE.strftime('%Y-%m-%d')
    end_date = (TARGET_DATE + timedelta(days=1)).strftime('%Y-%m-%d')
    
    soil_collection = dataset.select('volumetric_soil_water_layer_1') \
                            .filterDate(start_date, end_date) \
                            .filterBounds(aoi)
    
    count = soil_collection.size().getInfo()
    print(f" Found {count} hourly images")
    
    if count == 0:
        print(" No data found!")
        return []
    
    # Get image list
    image_list = soil_collection.toList(count)
    
    # Download each hour
    print(f"\n Downloading and processing {count} hours...")
    
    output_files = []
    all_data_for_normalization = []
    temp_files = []
    
    # First pass: Download all data
    print("\n   Phase 1: Downloading data...")
    for i in range(count):
        image = ee.Image(image_list.get(i))
        
        # Get timestamp
        timestamp = ee.Date(image.get('system:time_start')).format('YYYY-MM-dd_HH:mm').getInfo()
        hour = int(timestamp.split('_')[1].split(':')[0])
        
        print(f"   [{i+1}/{count}] Hour {hour:02d}:00 - downloading...", end='')
        
        # Get download URL
        url = image.getDownloadURL({
            'scale': 1000,  # ~1km resolution
            'crs': 'EPSG:4326',
            'region': aoi,
            'format': 'GEO_TIFF'
        })
        
        # Download with requests
        response = requests.get(url, timeout=300)
        
        if response.status_code != 200:
            print(f"  Failed")
            continue
        
        # Save temporary file
        temp_file = OUTPUT_DIR / f"temp_{hour:02d}.tif"
        with open(temp_file, 'wb') as f:
            f.write(response.content)
        
        # Read data for normalization
        with rasterio.open(temp_file) as src:
            data = src.read(1)
            valid_data = data[~np.isnan(data)]
            if len(valid_data) > 0:
                all_data_for_normalization.extend(valid_data.flatten())
        
        temp_files.append((temp_file, hour))
        print(f" ")
        
        time.sleep(0.5)
    
    # Calculate global min/max
    print("\n   Phase 2: Calculating normalization range...")
    global_min = np.min(all_data_for_normalization)
    global_max = np.max(all_data_for_normalization)
    print(f"   Range: {global_min:.4f} - {global_max:.4f} m³/m³")
    
    # Second pass: Reproject and normalize
    print("\n   Phase 3: Reprojecting and normalizing...")
    
    for temp_file, hour in temp_files:
        print(f"   Hour {hour:02d}:00 - processing...", end='')
        
        # Read and reproject
        with rasterio.open(temp_file) as src:
            # Calculate transform
            transform, width, height = calculate_default_transform(
                src.crs,
                TARGET_CRS,
                src.width,
                src.height,
                *src.bounds
            )
            
            # Read data
            data = src.read(1)
            
            # Create output array
            reprojected = np.zeros((height, width), dtype=np.float32)
            
            # Reproject
            reproject(
                source=data,
                destination=reprojected,
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=transform,
                dst_crs=TARGET_CRS,
                resampling=Resampling.bilinear
            )
            
            # Normalize
            wetness = (reprojected - global_min) / (global_max - global_min)
            wetness = np.clip(wetness, 0, 1)
            
            # Output file
            date_str = TARGET_DATE.strftime('%Y%m%d')
            output_file = OUTPUT_DIR / f"wf_{date_str}_{hour:02d}.tif"
            
            # Write final raster
            with rasterio.open(
                output_file,
                'w',
                driver='GTiff',
                height=height,
                width=width,
                count=1,
                dtype=rasterio.float32,
                crs=TARGET_CRS,
                transform=transform,
                compress='lzw'
            ) as dst:
                dst.write(wetness.astype(rasterio.float32), 1)
        
        # Clean up temp file
        temp_file.unlink()
        
        output_files.append(output_file)
        print(f"  Range: {wetness.min():.3f} - {wetness.max():.3f}")
    
    return output_files

# =
# VERIFY
# =

def verify_outputs(files):
    """Verify outputs"""
    
    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)
    
    for idx in [0, -1]:
        if idx < len(files):
            with rasterio.open(files[idx]) as src:
                print(f"\n {files[idx].name}")
                print(f"   CRS: {src.crs}")
                print(f"   Size: {src.width} x {src.height}")
                
                data = src.read(1)
                print(f"   Range: {data.min():.3f} - {data.max():.3f}")

# =
# MAIN
# =

def main():
    """Main execution"""
    
    # Initialize
    if not initialize_ee():
        print("\n Cannot initialize Earth Engine")
        return
    
    try:
        # Download and process
        files = download_and_process()
        
        if not files:
            print("\n No files created")
            return
        
        # Verify
        verify_outputs(files)
        
        # Summary
        print("\n" + "=" * 70)
        print(" SUCCESS -   DOWNLOAD COMPLETE!")
        print("=" * 70)
        
        print(f"\n Location: {OUTPUT_DIR}")
        print(f" Files created: {len(files)}")
        print(f"\n Properties:")
        print(f"   - CRS: {TARGET_CRS}")
        print(f"   - Values: 0-1 (wetness factor)")
    
        
    except Exception as e:
        print(f"\n Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

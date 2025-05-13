import logging
import os
import posixpath
import warnings

from rasterio.errors import NotGeoreferencedWarning

from water_quality.cgls_lwq.constants import MANIFEST_FILE_URLS, MEASUREMENTS
from water_quality.cgls_lwq.download_cogs import get_expected_cog_url
from water_quality.cgls_lwq.netcdf import (
    get_netcdf_urls_from_manifest,
)
from water_quality.cgls_lwq.tiles import (
    get_africa_tiles,
)
from water_quality.io import (
    find_geotiff_files,
    get_filesystem,
    is_local_path,
)
from water_quality.logs import setup_logging

# Suppress the warning
warnings.filterwarnings("ignore", category=NotGeoreferencedWarning)

product_name = "cgls_lwq300_2002_2012"
cog_output_dir = f"s3://deafrica-input-datasets/{product_name}/"
stac_output_dir = f"s3://deafrica-input-datasets/{product_name}/"
dryrun = True

# Setup logging level
setup_logging()
log = logging.getLogger(__name__)

# Read urls available for the product
all_netcdf_urls = get_netcdf_urls_from_manifest(MANIFEST_FILE_URLS[product_name])
log.info(f"Found {len(all_netcdf_urls)} netcdf urls in the manifest file")

# Define the tiles over Africa
if "300m" in all_netcdf_urls[0]:
    grid_res = 300
elif "100m" in all_netcdf_urls[0]:
    grid_res = 100

tiles = get_africa_tiles(grid_res)

measurements = MEASUREMENTS[product_name]

log.info(f"Getting the expected cog files to exist in {cog_output_dir}")
expected_cogs = []
for idx, netcdf_url in enumerate(all_netcdf_urls):
    log.info(f"Processing {netcdf_url} {idx + 1}/{len(all_netcdf_urls)}")
    for measurement_name in measurements:
        for tile in tiles:
            tile_idx, tile_geobox = tile
            expected_output_cog_url = get_expected_cog_url(
                output_dir=cog_output_dir,
                source_netcdf_url=netcdf_url,
                measurement_name=measurement_name,
                tile_index=tile_idx,
            )
            expected_cogs.append(expected_output_cog_url)
log.info("Done")
log.info(f"Expecting {len(expected_cogs)} cog files in {cog_output_dir}")

if is_local_path(cog_output_dir):
    expected_dataset_paths = list(set(os.path.dirname(i) for i in expected_cogs))
else:
    expected_dataset_paths = list(set(posixpath.dirname(i) for i in expected_cogs))
log.info(f"Expecting {len(expected_cogs)} datasets in {cog_output_dir}")

log.info(f"Getting the cog files actually in {cog_output_dir}")
existing_cogs = find_geotiff_files(cog_output_dir)
log.info("Done")
log.info(f"Found {len(expected_cogs)} cog files in {cog_output_dir}")

if is_local_path(cog_output_dir):
    existing_dataset_paths = list(set(os.path.dirname(i) for i in existing_cogs))
else:
    existing_dataset_paths = list(set(posixpath.dirname(i) for i in existing_cogs))
log.info(f"Found {len(expected_cogs)} cog files in {cog_output_dir}")

dirs_to_delete = [i for i in existing_dataset_paths if i not in expected_dataset_paths]

fs = get_filesystem(cog_output_dir, anon=False)
for dir_path in dirs_to_delete:
    if dryrun:
        log.info(f"Dryrun: delete {dir_path}")
    else:
        fs.rm(dir_path, recursive=True)
        log.info(f"Deleted {dir_path}")

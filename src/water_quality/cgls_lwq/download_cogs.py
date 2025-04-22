"""
Download the Copernicus Global Land Service Lake Water Quality datasets,
crop and convert to Cloud Optimized Geotiffs, and push to an S3 bucket.
"""

import logging
import sys
import warnings
from datetime import datetime

import click
import numpy as np
import requests
import rioxarray
from odc.geo.xr import assign_crs
from rasterio.errors import NotGeoreferencedWarning

from water_quality.cgls_lwq.constants import AFRICA_BBOX, MANIFEST_FILE_URLS, MEASUREMENTS
from water_quality.cgls_lwq.netcdf import (
    get_netcdf_subdatasets_uris,
    parse_netcdf_subdatasets_uri,
    parse_netcdf_url,
)
from water_quality.io import (
    check_directory_exists,
    check_file_exists,
    get_filesystem,
    join_urlpath,
)
from water_quality.logs import logging_setup

# Suppress the warning
warnings.filterwarnings("ignore", category=NotGeoreferencedWarning)


def get_output_cog_url(output_dir: str, netcdf_subdataset_uri: str) -> str:
    _, _, netcdf_url, subdataset_variable = parse_netcdf_subdatasets_uri(netcdf_subdataset_uri)
    filename_prefix, acronym, date_str, area, sensor, version, _ = parse_netcdf_url(netcdf_url)
    date = datetime.strptime(date_str, "%Y%m%d%H%M%S")
    year = str(date.year)
    month = f"{date.month:02d}"

    file_name = f"{filename_prefix}_{acronym}_{date_str}_{area}_{sensor}_{version}_{subdataset_variable}.tif"

    parent_dir = join_urlpath(output_dir, year, month)
    if not check_directory_exists(parent_dir):
        fs = get_filesystem(parent_dir, anon=False)
        fs.makedirs(parent_dir, exist_ok=True)

    output_cog_url = join_urlpath(parent_dir, file_name)
    return output_cog_url


@click.command(
    "download-cogs",
    help="Download the Copernicus Global Land Service Lake Water Quality datasets,"
    "crop and convert to Cloud Optimized Geotiffs, and push to an S3 bucket.",
    no_args_is_help=True,
)
@click.option(
    "--product-name",
    type=click.Choice(list(MANIFEST_FILE_URLS.keys()), case_sensitive=True),
    help="Name of the product to generate the stac item files for",
)
@click.option(
    "--cog-output-dir",
    type=str,
    help="Directory to write the cog files to",
)
@click.option("--overwrite/--no-overwrite", default=False, show_default=True)
@click.option(
    "--max-parallel-steps",
    default=1,
    show_default=True,
    type=int,
    help="Maximum number of parallel steps/pods to have in the workflow.",
)
@click.option(
    "--worker-idx",
    default=0,
    show_default=True,
    type=int,
    help="Sequential index which will be used to define the range of geotiffs the pod will work with.",
)
@click.option("-v", "--verbose", default=1, count=True)
def download_cogs(
    product_name: str,
    cog_output_dir: str,
    overwrite: bool,
    max_parallel_steps: int,
    worker_idx: int,
    verbose: int,
):
    # Setup logging level
    logging_setup(verbose)
    log = logging.getLogger(__name__)

    if product_name not in MANIFEST_FILE_URLS.keys():
        raise NotImplementedError(
            f"Manifest file url not configured for the product {product_name}"
        )

    # Read urls available for the product
    r = requests.get(MANIFEST_FILE_URLS[product_name])
    netcdf_urls = r.text.splitlines()

    # TODO: Remove filter by year
    # filter to 2011 only
    netcdf_urls = [i for i in netcdf_urls if "/2011/" in i]
    log.info(f"Found {len(netcdf_urls)} netcdf urls in the manifest file")

    # Split files equally among the workers
    task_chunks = np.array_split(np.array(netcdf_urls), max_parallel_steps)
    task_chunks = [chunk.tolist() for chunk in task_chunks]
    task_chunks = list(filter(None, task_chunks))

    # In case of the index being bigger than the number of positions in the array, the extra POD isn't necessary
    if len(task_chunks) <= worker_idx:
        log.warning(f"Worker {worker_idx} Skipped!")
        sys.exit(0)

    log.info(f"Executing worker {worker_idx}")

    dataset_paths = task_chunks[worker_idx]

    log.info(f"Generating COG files for the product {product_name}")

    for idx, netdf_url in enumerate(dataset_paths):
        log.info(f"Generating cog files for {netdf_url} {idx + 1}/{len(dataset_paths)}")

        # Get the subdatasets in the netcdf
        netcdf_subdatasets_uris = get_netcdf_subdatasets_uris(netdf_url)
        # Filter by required measurements
        netcdf_subdatasets_uris = {
            k: v for k, v in netcdf_subdatasets_uris.items() if k in MEASUREMENTS
        }
        # Check
        assert len(netcdf_subdatasets_uris) == len(MEASUREMENTS)

        for var, subdataset_uri in netcdf_subdatasets_uris.items():
            subdaset_cog_file = get_output_cog_url(cog_output_dir, subdataset_uri)
            if not overwrite:
                if check_file_exists(subdaset_cog_file):
                    log.info(
                        f"{subdaset_cog_file} exists! Skipping cog file generation for {subdataset_uri}"
                    )
                    continue

            # Load the netcdf url
            da = rioxarray.open_rasterio(subdataset_uri).squeeze(dim="time")
            attrs = da.attrs
            # Assign crs
            da = assign_crs(da, da.rio.crs, crs_coord_name="crs")
            # Subset to Africa
            ulx, uly, lrx, lry = AFRICA_BBOX
            # Note: lats are upside down!
            da = da.sel(y=slice(uly, lry), x=slice(ulx, lrx))

            # Write cog files
            cog_bytes = da.odc.write_cog(fname=":mem:", overwrite=overwrite, tags=attrs)
            fs = get_filesystem(subdaset_cog_file, anon=False)
            with fs.open(subdaset_cog_file, "wb") as f:
                f.write(cog_bytes)
            log.info(f"Written COG to {subdaset_cog_file}")

"""
Create per dataset metadata (stac files) for the Copernicus Global Land Service -
Lake Water Quality datasets.
"""

import json
import logging
import os
import sys
from pathlib import Path

import click
import numpy as np
import requests
import rioxarray
from odc.geo.xr import assign_crs
from pyproj import CRS
from tqdm import tqdm

from water_quality.cgls_lwq.constants import MANIFEST_FILE_URLS
from water_quality.io import get_filesystem, is_local_path, join_urlpath
from water_quality.logs import logging_setup


@click.command(
    "create-stac-files",
    help="Create per dataset metadata (stac files) for Copernicus Global "
    "Land Service Lake Water Quality datasets.",
    no_args_is_help=True,
)
@click.option(
    "--product-name",
    type=click.Choice(list(MANIFEST_FILE_URLS.keys()), case_sensitive=True),
    help="Name of the product to generate the stac item files for",
)
@click.option(
    "--product-yaml", type=str, help="File path or URL to the product definition yaml file"
)
@click.option(
    "--stac-output-dir",
    type=str,
    help="Directory to write the stac files docs to",
)
@click.option("--overwrite/--no-overwrite", default=False)
@click.option(
    "--max-parallel-steps",
    default=1,
    type=int,
    help="Maximum number of parallel steps/pods to have in the workflow.",
)
@click.option(
    "--worker-idx",
    default=0,
    type=int,
    help="Sequential index which will be used to define the range of geotiffs the pod will work with.",
)
@click.option("-v", "--verbose", default=1, count=True)
def create_stac_files(
    product_name: str,
    product_yaml: str,
    stac_output_dir: str,
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

    # Read urls available the prooduct
    r = requests.get(MANIFEST_FILE_URLS[product_name])
    netcdf_urls = r.text.splitlines()
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

    log.info(f"Generating stac files for the product {product_name}")

    for idx, dataset_path in enumerate(dataset_paths):
        log.info(f"Generating stac file for {dataset_path} {idx + 1}/{len(dataset_paths)}")

        if is_local_path(dataset_path):
            dataset_path = Path(dataset_path).resolve()

        # Define stac file

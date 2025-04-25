"""
Create per dataset metadata (stac files) for the Copernicus Global Land Service -
Lake Water Quality datasets.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import click
import numpy as np
import requests
from eodatasets3.serialise import to_path  # noqa F401
from eodatasets3.stac import to_stac_item

from water_quality.cgls_lwq.constants import MANIFEST_FILE_URLS
from water_quality.cgls_lwq.geotiff import parse_geotiff_url
from water_quality.cgls_lwq.netcdf import parse_netcdf_url
from water_quality.cgls_lwq.prepare_metadata import prepare_dataset
from water_quality.io import (
    check_directory_exists,
    check_file_exists,
    get_filesystem,
    is_local_path,
    join_urlpath,
)
from water_quality.logs import logging_setup


def get_stac_item_destination_url(output_dir: str, geotiff_url: str) -> str:
    (
        filename_prefix,
        acronym,
        date_str,
        area,
        sensor,
        version,
        tile_index_str,
        subdataset_variable,
        _,
    ) = parse_geotiff_url(geotiff_url)

    date = datetime.strptime(date_str, "%Y%m%d%H%M%S")
    year = str(date.year)
    month = f"{date.month:02d}"
    day = f"{date.day:02d}"

    file_name = f"{filename_prefix}_{acronym}_{date_str}_{area}_{sensor}_{version}_{tile_index_str}_{subdataset_variable}.stac-item.json"

    parent_dir = join_urlpath(
        output_dir,
        tile_index_str_x,
        tile_index_str_y,
        year,
        month,
        day,
    )
    if not check_directory_exists(parent_dir):
        fs = get_filesystem(parent_dir, anon=False)
        fs.makedirs(parent_dir, exist_ok=True)

    stac_item_destination_url = join_urlpath(parent_dir, file_name)
    return stac_item_destination_url


def get_eo3_dataset_doc_file_path(
    output_dir: str, netcdf_url: str, write_eo3_dataset_doc: bool
) -> str:
    filename_prefix, acronym, date_str, area, sensor, version, _ = parse_netcdf_url(netcdf_url)
    date = datetime.strptime(date_str, "%Y%m%d%H%M%S")
    year = str(date.year)
    month = f"{date.month:02d}"
    file_name = (
        f"{filename_prefix}_{acronym}_{date_str}_{area}_{sensor}_{version}.odc-metadata.yaml"
    )

    parent_dir = join_urlpath(output_dir, year, month)
    if write_eo3_dataset_doc:
        if not check_directory_exists(parent_dir):
            fs = get_filesystem(parent_dir, anon=False)
            fs.makedirs(parent_dir, exist_ok=True)

    eo3_dataset_doc_file_path = join_urlpath(parent_dir, file_name)
    return eo3_dataset_doc_file_path


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
@click.option(
    "--write-eo3/--no-write-eo3",
    default=False,
    show_default=True,
    help="Whether to write eo3 dataset documents before they are converted to stac.",
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
    write_eo3: bool,
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

    # Write the eo3 dataset document to disk

    for idx, dataset_path in enumerate(dataset_paths):
        log.info(f"Generating stac file for {dataset_path} {idx + 1}/{len(dataset_paths)}")

        if is_local_path(dataset_path):
            dataset_path = Path(dataset_path).resolve()

        stac_item_destination_url = get_stac_item_destination_url(stac_output_dir, dataset_path)
        if not overwrite:
            if check_file_exists(stac_item_destination_url):
                log.info(
                    f"{stac_item_destination_url} exists! Skipping stac file generation for {dataset_path}"
                )
                continue

        # Dataset docs
        dataset_doc_output_path = get_eo3_dataset_doc_file_path(
            stac_output_dir, dataset_path, write_eo3
        )

        dataset_doc = prepare_dataset(dataset_path, product_yaml, dataset_doc_output_path)

        if write_eo3:
            to_path(Path(dataset_doc_output_path), dataset_doc)

        # Convert dataset doc to stac item
        stac_item = to_stac_item(
            dataset=dataset_doc, stac_item_destination_url=str(stac_item_destination_url)
        )

        # Write stac file to disk.
        fs = get_filesystem(str(stac_item_destination_url), anon=False)
        with fs.open(str(stac_item_destination_url), "w") as f:
            json.dump(stac_item, f, indent=2)  # `indent=4` makes it human-readable

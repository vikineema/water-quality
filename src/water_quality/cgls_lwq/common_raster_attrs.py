import json
import logging
import os

import click
import requests
import rioxarray
from odc.geo.xr import assign_crs
from pyproj import CRS
from tqdm import tqdm

from water_quality.cgls_lwq.constants import MANIFEST_FILE_URLS, MEASUREMENTS
from water_quality.cgls_lwq.netcdf import get_netcdf_subdatasets_uris
from water_quality.io import get_filesystem, is_local_path, join_url
from water_quality.logs import setup_logging


@click.command(
    "get-common-raster-attrs",
    help="Get common attrs for all datasets for a CGLS Lake Water Quality product.",
    no_args_is_help=True,
)
@click.option(
    "--product-name",
    type=click.Choice(list(MANIFEST_FILE_URLS.keys()), case_sensitive=True),
    help="Name of the product to get storage parameters for",
)
@click.option(
    "--output-dir",
    type=str,
    help="Directory to write the unique storage parameters text file to",
)
@click.option("-v", "--verbose", default=1, count=True)
def get_common_raster_attrs(
    product_name: str,
    output_dir: str,
    verbose: int,
):
    # Setup logging level
    setup_logging(verbose)
    log = logging.getLogger(__name__)

    if product_name not in MANIFEST_FILE_URLS.keys():
        raise NotImplementedError(
            f"Manifest file url not configured for the product {product_name}"
        )

    if product_name not in MEASUREMENTS.keys():
        raise NotImplementedError(
            f"Required measurements not configured for the product {product_name}"
        )

    if is_local_path(str(output_dir)):
        output_dir = os.path.abspath(output_dir)

    # Get the file where to store the  storage parameters
    output_file_path = join_url(output_dir, product_name, "storage_parameters.txt")
    # Create the parent directories if they do not exist
    fs = get_filesystem(output_file_path, anon=False)
    parent_dir = fs._parent(output_file_path)
    fs.makedirs(parent_dir, exist_ok=True)

    # Read urls available the prooduct
    r = requests.get(MANIFEST_FILE_URLS[product_name])
    netcdf_urls = r.text.splitlines()
    log.info(f"Found {len(netcdf_urls)} netcdf urls in the manifest file")

    storage_parameters_list = []
    for netdf_url in tqdm(iterable=netcdf_urls, total=len(netcdf_urls)):
        # Get the subdatasets in the netcdf
        netcdf_subdatasets_uris = get_netcdf_subdatasets_uris(netdf_url)
        # Filter by required measurements
        netcdf_subdatasets_uris = {
            k: v for k, v in netcdf_subdatasets_uris.items() if k in MEASUREMENTS[product_name]
        }
        # Check
        assert len(netcdf_subdatasets_uris) == len(MEASUREMENTS[product_name])

        measurement_attrs = {}
        for var, subdatasets_uri in netcdf_subdatasets_uris:
            # Load the netcdf url
            da = rioxarray.open_rasterio(subdatasets_uri)
            # Add a geobox to the dataset
            da = assign_crs(da, da.rio.crs, crs_coord_name="crs")

            crs = ":".join(CRS(da.odc.geobox.crs).to_authority())  # Authority name: code for crs
            res_x = da.odc.geobox.resolution.x
            res_y = da.odc.geobox.resolution.y
            measurement_attrs[var] = dict(
                crs=crs,
                res_x=str(res_x),
                res_y=str(res_y),
                dtype=str(da.dtype),
                units=da.attrs["units"],
                no_data_value=str(da.attrs["_FillValue"]),
                add_offset=str(da.attrs["add_offset"]),
                scale_factor=str(da.attrs["scale_factor"]),
            )

        storage_parameters_list.append(measurement_attrs)

    # Convert dicts to JSON strings to create a unique set
    unique_storage_parameters = [
        json.loads(s) for s in {json.dumps(d, sort_keys=True) for d in storage_parameters_list}
    ]
    storage_parameters_json_array = json.dumps(unique_storage_parameters)

    with fs.open(output_file_path, "w") as file:
        file.write(storage_parameters_json_array)
    log.info(f"Tasks chunks written to {output_file_path}")

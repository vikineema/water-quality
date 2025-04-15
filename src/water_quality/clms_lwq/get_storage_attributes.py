import json
import logging
import os

import click
import requests
import rioxarray
from odc.geo.xr import assign_crs
from pyproj import CRS
from tqdm import tqdm

from water_quality.io import get_filesystem, is_local_path, join_urlpath
from water_quality.logs import logging_setup

# map product name to manifest file url
MANIFEST_FILE_URLS = {
    "cgls_LWQ300_v1_300": "https://globalland.vito.be/download/manifest/lwq_300m_v1_10daily-reproc_netcdf/manifest_clms_global_lwq_300m_v1_10daily-reproc_netcdf_latest.txt"
}
# Bands in the netcdf file to check
MEASUREMENTS = [
    "num_obs",
    "first_obs",
    "trophic_state_index",
    "last_obs",
    "n_obs_quality_risk_sum",
    "stats_valid_obs_tsi_sum",
    "stats_valid_obs_turbidity_sum",
    "turbidity_mean",
    "turbidity_sigma",
]

# Setup logging
logging_setup(verbose=3)

log = logging.getLogger(__name__)


@click.command(
    "get-storage-parameters", help="Get common parameters for datasets.", no_args_is_help=True
)
@click.option(
    "--product-name",
    type=click.Choice(["cgls_LWQ300_v1_300"], case_sensitive=True),
    help="Name of the product to get storage parameters for",
)
@click.option(
    "--output-dir",
    type=str,
    help="Directory to write the unique storage parameters text file to",
)
def get_storage_parameters(
    product_name: str,
    output_dir: str,
):
    if product_name not in MANIFEST_FILE_URLS.keys():
        raise NotImplementedError(
            f"Manifest file url not configured for the product {product_name}"
        )

    if is_local_path(str(output_dir)):
        output_dir = os.path.abspath(output_dir)

    # Get the file where to store the  storage parameters
    output_file_path = join_urlpath(output_dir, product_name, "storage_parameters.txt")
    # Create the parent directories if they do not exist
    fs = get_filesystem(output_file_path, anon=False)
    parent_dir = fs._parent(output_file_path)
    fs.makedirs(parent_dir, exist_ok=True)

    # Read urls available the prooduct
    r = requests.get(MANIFEST_FILE_URLS[product_name])
    netcdf_urls = r.text.splitlines()
    log.info(f"Found {len(netcdf_urls)} netcdf urls in the manifest file")

    storage_parameters_list = []
    for url in tqdm(iterable=netcdf_urls, total=len(netcdf_urls)):
        # Load the netcdf url
        ds = rioxarray.open_rasterio(url)
        # Add a geobox to the dataset
        ds = assign_crs(ds, ds.rio.crs, crs_coord_name="crs")

        crs = ":".join(CRS(ds.odc.geobox.crs).to_authority())  # Authority name: code for crs
        res_x = ds.odc.geobox.resolution.x
        res_y = ds.odc.geobox.resolution.y

        measurement_attrs = {}
        for var in MEASUREMENTS:
            da = ds[var]
            measurement_attrs[var] = dict(
                dtye=str(da.dtype),
                units=da.attrs["units"],
                no_data_value=str(da.attrs["_FillValue"]),
                add_offset=str(da.attrs["add_offset"]),
                scale_factor=str(da.attrs["scale_factor"]),
            )

        item = {
            "crs": crs,
            "res_x": str(res_x),
            "res_y": str(res_y),
            "measurements": measurement_attrs,
        }
        storage_parameters_list.append(item)

    # Convert dicts to JSON strings to create a unique set
    unique_storage_parameters = [
        json.loads(s) for s in {json.dumps(d, sort_keys=True) for d in storage_parameters_list}
    ]
    storage_parameters_json_array = json.dumps(unique_storage_parameters)

    with fs.open(output_file_path, "w") as file:
        file.write(storage_parameters_json_array)
    log.info(f"Tasks chunks written to {output_file_path}")

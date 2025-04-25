"""
Functions to parse info from Copernicus Global Land Service -
Lake Water Quality netcdf files
"""

import os
import posixpath
import re
from urllib.parse import urlparse

import rasterio


def parse_netcdf_url(netcdf_url: str) -> tuple[str]:
    # Get the file name
    filename = posixpath.basename(urlparse(netcdf_url).path)

    # Get the file extension
    _, extension = os.path.splitext(filename)

    # File naming convention in
    # c_gls_<Acronym>_<YYYYMMDDHHmm>_<AREA>_<SENSOR>_<Version>.<EXTENSION>
    filename_prefix = "c_gls"
    acronym, date_str, area, sensor, version = (
        filename.removeprefix(filename_prefix + "_").removesuffix(extension).split("_")
    )
    extension = extension.removeprefix(".")
    return filename_prefix, acronym, date_str, area, sensor, version, extension


def parse_netcdf_subdatasets_uri(netcdf_uri: str) -> tuple[str]:
    # subdaset uri format driver:"filename":subdataset_variable
    # or driver:/vsiprefix/URL[:subdataset_variable]
    driver = netcdf_uri.split(":")[0]
    assert driver.lower() == "netcdf"

    subdataset_variable = netcdf_uri.split(":")[-1]

    netcdf_url = netcdf_uri.removeprefix(f"{driver}:").removesuffix(f":{subdataset_variable}")

    matches = re.search(r"^/vsi[^/]+/", netcdf_url)
    if matches is None:
        vsiprefix = ""
    else:
        vsiprefix = matches.group()  # .strip("/")

    netcdf_url = netcdf_url.replace(vsiprefix, "")
    return driver, vsiprefix, netcdf_url, subdataset_variable


def get_netcdf_subdataset_variable(netcdf_uri: str) -> tuple[str]:
    _, _, _, subdataset_variable = parse_netcdf_subdatasets_uri(netcdf_uri)
    return subdataset_variable


def get_netcdf_subdatasets_uris(netcdf_url: str) -> list[str]:
    with rasterio.open(netcdf_url, "r") as src:
        subdatasets = src.subdatasets
    netcdf_subdatasets_uris = {get_netcdf_subdataset_variable(i): i for i in subdatasets}
    return netcdf_subdatasets_uris


def get_netcdf_subdatasets_names(netcdf_url: str) -> list[str]:
    netcdf_subdatasets_names = list(get_netcdf_subdatasets_uris(netcdf_url).keys())
    return netcdf_subdatasets_names

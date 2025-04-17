"""
Functions to parse info from Copernicus Global Land Service -
Lake Water Quality netcdf files
"""

import os
import posixpath
from urllib.parse import urlparse

import rasterio
import rioxarray


def parse_netcdf_url(netcdf_url: str) -> tuple[str]:
    # Get the file name
    filename = posixpath.basename(urlparse(netcdf_url).path)

    # Get the file extension
    _, extension = os.path.splitext(filename)

    # File naming convention in
    # c_gls_<Acronym>_<YYYYMMDDHHmm>_<AREA>_<SENSOR>_<Version>.<EXTENSION>
    filename_prefix = "c_gls"
    acronym, date, area, sensor, version = (
        filename.removeprefix(filename_prefix + "_").removesuffix(extension).split("_")
    )
    extension = extension.removeprefix(".")
    return filename_prefix, acronym, date, area, sensor, version, extension


def get_common_attrs(netcdf_url: str) -> dict:
    common_attrs = rioxarray.open_rasterio(netcdf_url).attrs
    return common_attrs


def get_subdataset_variable(netcdf_uri: str) -> tuple[str]:
    # format driver:/vsiprefix/URL[:subdataset_variable]
    subdataset_variable = netcdf_uri.split(":")[-1]
    return subdataset_variable


def get_netcdf_subdatasets(netcdf_url: str) -> list[str]:
    with rasterio.open(netcdf_url, "r") as src:
        subdatasets = src.subdatasets

    subdataset_variables = [get_subdataset_variable(i) for i in subdatasets]
    return subdataset_variables

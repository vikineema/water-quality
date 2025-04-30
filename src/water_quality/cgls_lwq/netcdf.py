"""
Functions to parse info from Copernicus Global Land Service -
Lake Water Quality netcdf files
"""

import os
import posixpath
import re

import rasterio
from osgeo import gdal
from rasterio.errors import RasterioIOError

from water_quality.cgls_lwq.constants import NAMING_PREFIX
from water_quality.io import get_gdal_vsi_prefix, is_local_path


def parse_netcdf_url(netcdf_url: str) -> tuple[str]:
    """
    Get the filename components of a CGLS Lake Water Quality
    netcdf url.

    Parameters
    ----------
    netcdf_url : str
        CGLS Lake Water Quality netcdf url

    Returns
    -------
    tuple[str]
        Filename components of a CGLS Lake Water Quality netcdf url.
    """
    if is_local_path(netcdf_url):
        filename = os.path.basename(netcdf_url)
    else:
        filename = posixpath.basename(netcdf_url)

    # Get the file extension
    _, extension = os.path.splitext(filename)

    # File naming convention in
    # c_gls_<Acronym>_<YYYYMMDDHHmm>_<AREA>_<SENSOR>_<Version>.<EXTENSION>
    parts = filename.removeprefix(NAMING_PREFIX).removesuffix(extension).split("_")
    parts = list(filter(None, parts))
    acronym, date_str, area, sensor, version = parts
    extension = extension.removeprefix(".")

    return NAMING_PREFIX, acronym, date_str, area, sensor, version, extension


def parse_netcdf_subdatasets_uri(netcdf_uri: str) -> tuple[str]:
    """
    Parse a CGLS Lake Water Quality netcdf subdaset URI to get the driver,
    GDAL VFS prefix, parent netcdf url and the name of the subdatset.

    Parameters
    ----------
    netcdf_uri : str
        CGLS Lake Water Quality netcdf subdaset URI

    Returns
    -------
    tuple[str]
        Driver, GDAL VFS prefix, parent netcdf url and the name of the subdatset
    """
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
    """Get the name of a CGLS Lake Water Quality netcdf subdaset from
    its URI.

    Parameters
    ----------
    netcdf_uri : str
        CGLS Lake Water Quality netcdf subdaset URI.

    Returns
    -------
    tuple[str]
        Name of the subdataset.
    """
    _, _, _, subdataset_variable = parse_netcdf_subdatasets_uri(netcdf_uri)
    return subdataset_variable


def get_netcdf_subdatasets_uris(netcdf_url: str) -> dict[str, str]:
    """Get a dictionary mapping a subdatset's name to its URI for all
    subddatasets from a CGLS Lake Water Quality netcdf file

    Parameters
    ----------
    netcdf_url : str
        URL to the GLS Lake Water Quality netcdf file

    Returns
    -------
    dict[str, str]
        Mapping of name to URI for all subdatasets in the CGLS Lake Water Quality netcdf file
    """

    with rasterio.open(netcdf_url, "r") as src:
        subdatasets = src.subdatasets

    netcdf_subdatasets_uris = {get_netcdf_subdataset_variable(i): i for i in subdatasets}

    return netcdf_subdatasets_uris


def get_netcdf_subdatasets_names(netcdf_url: str) -> list[str]:
    """Get a list of all the subdatasets names in a
    CGLS Lake Water Quality netcdf file

    Parameters
    ----------
    netcdf_url : str
        URL to the GLS Lake Water Quality netcdf file

    Returns
    -------
    list[str]
        List of all the subdatasets names in the
        CGLS Lake Water Quality netcdf file
    """
    netcdf_subdatasets_names = list(get_netcdf_subdatasets_uris(netcdf_url).keys())
    return netcdf_subdatasets_names

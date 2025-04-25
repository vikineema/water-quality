import os
import posixpath
from urllib.parse import urlparse

from water_quality.io import is_local_path


def parse_geotiff_url(geotiff_url: str) -> tuple[str]:
    if is_local_path(geotiff_url):
        filename = os.path.basename(geotiff_url)
    else:
        filename = posixpath.basename(urlparse(geotiff_url).path)

    # Get the file extension
    _, extension = os.path.splitext(filename)

    # File naming convention in
    # c_gls_<Acronym>_<YYYYMMDDHHmm>_<AREA>_<SENSOR>_<Version>_<tile_index_str>_<subdataset_variable>.<EXTENSION>
    filename_prefix = "c_gls"
    acronym, date_str, area, sensor, version, tile_index_str, *subdataset_variable = (
        filename.removeprefix(filename_prefix + "_").removesuffix(extension).split("_")
    )
    subdataset_variable = "_".join(subdataset_variable)
    extension = extension.removeprefix(".")
    return (
        filename_prefix,
        acronym,
        date_str,
        area,
        sensor,
        version,
        tile_index_str,
        subdataset_variable,
        extension,
    )

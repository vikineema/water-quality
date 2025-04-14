import os
import posixpath
from datetime import datetime
from urllib.parse import urlparse

from water_quality.io import join_urlpath


def get_output_fp(output_dir: str, url: str) -> str:
    # Get the file name
    filename = posixpath.basename(urlparse(url).path)
    # Get the file extension
    _, extension = os.path.splitext(filename)
    filename_prefix = "c_gls_"
    # File naming convention in
    # c_gls_<Acronym>_<YYYYMMDDHHmm>_<AREA>_<SENSOR>_<Version>.<EXTENSION>
    acronym, date, area, sensor, version = (
        filename.lstrip(filename_prefix).rstrip(extension).split("_")
    )
    date = datetime.strptime(date, "%y%m%d%H%M%S")

    output_file_path = join_urlpath(output_dir, str(date.year), f"{date.month:02d}", filename)

    return output_file_path

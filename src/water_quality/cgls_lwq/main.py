import click

from water_quality.cgls_lwq.common_raster_attrs import get_common_raster_attrs
from water_quality.cgls_lwq.download_cogs import download_cogs
from water_quality.cgls_lwq.metadata_generator import create_stac_files


@click.group(
    name="cgls_lwq",
    help="Run tools for Copernicus Global Land Service Lake Water Quality Products.",
)
def cgls_lwq():
    pass


cgls_lwq.add_command(get_common_raster_attrs)
cgls_lwq.add_command(create_stac_files)
cgls_lwq.add_command(download_cogs)

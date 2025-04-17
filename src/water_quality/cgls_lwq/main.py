import click

from water_quality.cgls_lwq.get_storage_attributes import get_storage_parameters
from water_quality.cgls_lwq.metadata_generator import create_stac_files


@click.group(
    name="cgls_lwq",
    help="Run tools for Copernicus Global Land Service Lake Water Quality Products.",
)
def cgls_lwq():
    pass


cgls_lwq.add_command(get_storage_parameters)
cgls_lwq.add_command(create_stac_files)

import click

from water_quality.clms_lwq.create_stac import create_stac_files
from water_quality.clms_lwq.get_storage_attributes import get_storage_parameters


@click.group(name="clms_lwq", help="Run tools for Copernicus Lake Water Quality Products.")
def clms_lwq():
    pass


clms_lwq.add_command(get_storage_parameters)
clms_lwq.add_command(create_stac_files)

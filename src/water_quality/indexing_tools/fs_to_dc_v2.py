import json
import logging
from pathlib import Path

import click
import datacube
import yaml
from datacube.index.hl import Doc2Dataset
from datacube.ui.click import environment_option, pass_config
from odc.apps.dc_tools.utils import (
    allow_unsafe,
    archive_less_mature,
    index_update_dataset,
    publish_action,
    statsd_gauge_reporting,
    statsd_setting,
    transform_stac,
    update_if_exists_flag,
)

from water_quality.indexing_tools.stac_to_eo3 import stac_transform

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s: %(levelname)s: %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S",
)


@click.command("fs-to-dc")
@environment_option
@pass_config
@click.argument("input_directory", type=str, nargs=1)
@update_if_exists_flag
@allow_unsafe
@archive_less_mature
@transform_stac
@statsd_setting
@publish_action
@click.option(
    "--glob",
    default=None,
    help="File system glob to use, defaults to **/*.yaml or **/*.json for STAC.",
)
def cli(
    cfg_env,
    input_directory,
    update_if_exists,
    allow_unsafe,
    stac,
    statsd_setting,
    glob,
    archive_less_mature,
    publish_action,
) -> None:
    dc = datacube.Datacube(env=cfg_env)
    doc2ds = Doc2Dataset(dc.index)

    if glob is None:
        glob = "**/*.json" if stac else "**/*.yaml"

    files_to_process = Path(input_directory).glob(glob)

    added, failed = 0, 0

    for in_file in files_to_process:
        with in_file.open() as f:
            try:
                if in_file.suffix in (".yml", ".yaml"):
                    metadata = yaml.safe_load(f)
                else:
                    metadata = json.load(f)
                # Do the STAC Transform if it's flagged
                stac_doc = None
                if stac:
                    stac_doc = metadata
                    metadata = stac_transform(metadata)
                index_update_dataset(
                    metadata,
                    in_file.absolute().as_uri(),
                    dc=dc,
                    doc2ds=doc2ds,
                    update_if_exists=update_if_exists,
                    allow_unsafe=allow_unsafe,
                    archive_less_mature=archive_less_mature,
                    publish_action=publish_action,
                    stac_doc=stac_doc,
                )
                added += 1
            except Exception:  # pylint: disable=broad-except
                logging.exception("Failed to add dataset %s", in_file)
                failed += 1

    logging.info("Added %s and failed %s datasets.", added, failed)
    if statsd_setting:
        statsd_gauge_reporting(added, ["app:fs_to_dc", "action:added"], statsd_setting)
        statsd_gauge_reporting(failed, ["app:fs_to_dc", "action:failed"], statsd_setting)


if __name__ == "__main__":
    cli()

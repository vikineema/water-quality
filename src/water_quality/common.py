import logging

from tqdm import tqdm

from water_quality.io import get_filesystem

log = logging.getLogger(__name__)


def download_file(url: str, output_file_path: str, verbose: bool = False):
    fs_url = get_filesystem(url)
    fs_output_file_path = get_filesystem(output_file_path, anon=False)

    # Create the parent directories if they do not exist
    parent_dir = fs_output_file_path._parent(output_file_path)
    fs_output_file_path.makedirs(parent_dir)

    fs_url.get(url, output_file_path)

    if verbose:
        log.info(f"Downloaded {output_file_path}")

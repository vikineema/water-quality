"""
Utilities for interacting with local, cloud (S3, GCS), and HTTP filesystems
"""

import logging
import os
import posixpath
import re

import fsspec
import requests
from fsspec.implementations.http import HTTPFileSystem
from fsspec.implementations.local import LocalFileSystem
from gcsfs import GCSFileSystem
from s3fs.core import S3FileSystem
from tqdm import tqdm

log = logging.getLogger(__name__)


def is_s3_path(path: str) -> bool:
    fs, _ = fsspec.core.url_to_fs(path)
    return isinstance(fs, S3FileSystem)


def is_gcsfs_path(path: str) -> bool:
    fs, _ = fsspec.core.url_to_fs(path)
    return isinstance(fs, GCSFileSystem)


def is_http_url(path: str) -> bool:
    fs, _ = fsspec.core.url_to_fs(path)
    return isinstance(fs, HTTPFileSystem)


def is_local_path(path: str) -> bool:
    fs, _ = fsspec.core.url_to_fs(path)
    return isinstance(fs, LocalFileSystem)


def join_urlpath(base, *paths) -> str:
    if is_local_path(base):
        return os.path.join(base, *paths)
    else:
        # Ensure urls join correctly
        return posixpath.join(base, *paths)


def get_filesystem(
    path: str,
    anon: bool = True,
) -> S3FileSystem | LocalFileSystem | GCSFileSystem:
    if is_s3_path(path=path):
        fs = S3FileSystem(anon=anon, s3_additional_kwargs={"ACL": "bucket-owner-full-control"})
    elif is_gcsfs_path(path=path):
        if anon:
            fs = GCSFileSystem(token="anon")
        else:
            fs = GCSFileSystem()
    elif is_http_url(path):
        fs = HTTPFileSystem()
    elif is_local_path(path=path):
        fs = LocalFileSystem()
    return fs


def check_file_exists(path: str) -> bool:
    fs = get_filesystem(path=path, anon=True)
    if fs.exists(path) and fs.isfile(path):
        return True
    else:
        return False


def check_directory_exists(path: str) -> bool:
    fs = get_filesystem(path=path, anon=True)
    if fs.exists(path) and fs.isdir(path):
        return True
    else:
        return False


def check_file_extension(path: str, accepted_file_extensions: list[str]) -> bool:
    _, file_extension = os.path.splitext(path)
    if file_extension.lower() in accepted_file_extensions:
        return True
    else:
        return False


def is_geotiff(path: str) -> bool:
    accepted_geotiff_extensions = [".tif", ".tiff", ".gtiff"]
    return check_file_extension(path=path, accepted_file_extensions=accepted_geotiff_extensions)


def find_geotiff_files(directory_path: str, file_name_pattern: str = ".*") -> list[str]:
    file_name_pattern = re.compile(file_name_pattern)

    fs = get_filesystem(path=directory_path, anon=True)

    geotiff_file_paths = []

    for root, dirs, files in fs.walk(directory_path):
        for file_name in files:
            if is_geotiff(path=file_name):
                if re.search(file_name_pattern, file_name):
                    geotiff_file_paths.append(os.path.join(root, file_name))
                else:
                    continue
            else:
                continue

    if is_s3_path(path=directory_path):
        geotiff_file_paths = [f"s3://{file}" for file in geotiff_file_paths]
    elif is_gcsfs_path(path=directory_path):
        geotiff_file_paths = [f"gs://{file}" for file in geotiff_file_paths]
    return geotiff_file_paths


def is_json(path: str) -> bool:
    accepted_json_extensions = [".json"]
    return check_file_extension(path=path, accepted_file_extensions=accepted_json_extensions)


def find_json_files(directory_path: str, file_name_pattern: str = ".*") -> list[str]:
    file_name_pattern = re.compile(file_name_pattern)

    fs = get_filesystem(path=directory_path, anon=True)

    json_file_paths = []

    for root, dirs, files in fs.walk(directory_path):
        for file_name in files:
            if is_json(path=file_name):
                if re.search(file_name_pattern, file_name):
                    json_file_paths.append(os.path.join(root, file_name))
                else:
                    continue
            else:
                continue

    if is_s3_path(path=directory_path):
        json_file_paths = [f"s3://{file}" for file in json_file_paths]
    elif is_gcsfs_path(path=directory_path):
        json_file_paths = [f"gs://{file}" for file in json_file_paths]
    return json_file_paths


def download_file_from_url(url: str, output_file_path: str, chunks: int = 100) -> str:
    """Download a file from a URL

    Parameters
    ----------
    url : str
        URL to download file from.
    output_file_path : str
        File path to download to.
    chunks : int, optional
        Chunk size in MB, by default 100

    Returns
    -------
    str
        The file path the file has been downloaded to.
    """
    fs = get_filesystem(output_file_path, anon=False)

    # Create the parent directories if they do not exist
    parent_dir = fs._parent(output_file_path)
    if not check_directory_exists(parent_dir):
        fs.makedirs(parent_dir, exist_ok=True)

    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        with fs.open(output_file_path, "wb") as f:
            with tqdm(
                desc=output_file_path,
                total=total,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                for chunk in r.iter_content(chunk_size=chunks * 1024**2):
                    size = f.write(chunk)
                    bar.update(size)

    return output_file_path


def get_gdal_vsi_prefix(file_path) -> str:
    # Based on file extension
    _, file_extension = os.path.splitext(file_path)
    if file_extension in [".zip"]:
        vsi_prefix_1 = "vsizip"
    elif file_extension in [".gz"]:
        vsi_prefix_1 = "vsigzip"
    elif file_extension in [".tar", ".tgz"]:
        vsi_prefix_1 = "vsitar"
    elif file_extension in [".7z"]:
        vsi_prefix_1 = "vsi7z"
    elif file_extension in [".rar"]:
        vsi_prefix_1 = "vsirar"
    else:
        vsi_prefix_1 = ""

    if vsi_prefix_1:
        vsi_prefix_1_file_path = f"/{vsi_prefix_1}/{file_path}"
    else:
        vsi_prefix_1_file_path = file_path

    # Network based
    if is_local_path(file_path):
        return vsi_prefix_1_file_path
    elif is_http_url(file_path):
        return f"/vsicurl/{vsi_prefix_1_file_path}"
    elif is_s3_path(file_path):
        return f"/vsis3/{vsi_prefix_1_file_path}"
    elif is_gcsfs_path(file_path):
        return f"/vsigs/{vsi_prefix_1_file_path}"
    else:
        NotImplementedError()

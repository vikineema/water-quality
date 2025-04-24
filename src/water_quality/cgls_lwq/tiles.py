import os
import re

from odc.geo import XY, Resolution
from odc.geo.geom import BoundingBox
from odc.geo.gridspec import GridSpec

from water_quality.cgls_lwq.constants import AFRICA_BBOX


def get_tile_index_tuple_from_str(string_: str) -> tuple[int, int]:
    """
    Get the tile index (x,y) from a string.

    Parameters
    ----------
    string_ : str
        String to search for a tile index

    Returns
    -------
    tuple[int, int]
        Found tile index (x,y).
    """
    x_pattern = re.compile(r"x\d{3}")
    y_pattern = re.compile(r"y\d{3}")

    tile_index_x_str = re.search(x_pattern, string_).group(0)
    tile_index_y_str = re.search(y_pattern, string_).group(0)

    tile_index_x = int(tile_index_x_str.lstrip("x"))
    tile_index_y = int(tile_index_y_str.lstrip("y"))

    tile_index = (tile_index_x, tile_index_y)

    return tile_index


def get_tile_index_str_from_tuple(tile_index_tuple: tuple[int, int]) -> str:
    """
    Convert a tile index tuple into the tile index string format
    x123_y123.

    Parameters
    ----------
    tile_index_tuple : tuple[int, int]
        Tile index tuple to convert to string.

    Returns
    -------
    str
        Tile index in string format x123_y123.
    """

    tile_index_x, tile_index_y = tile_index_tuple

    tile_index_str = f"x{tile_index_x:03d}_y{tile_index_y:03d}"

    return tile_index_str


def get_tile_index_tuple_from_filename(file_path: str) -> tuple[int, int]:
    """
    Search for a tile index in the base name of a file.

    Parameters
    ----------
    file_path : str
        File path to search tile index in.

    Returns
    -------
    tuple[int, int]
        Found tile index (x,y).
    """
    file_name = os.path.splitext(os.path.basename(file_path))[0]

    tile_id = get_tile_index_tuple_from_str(file_name)

    return tile_id


def get_africa_tiles(grid_res: int | float) -> list:
    """
    Get tiles over Africa extent.

    Parameters
    ----------
    grid_res : int | float
        Grid resolution in projected crs (EPSG:6933).

    Returns
    -------
    list
        List of tiles, each item contains the tile index and the tile geobox.
    """
    multiplier = 10
    gridspec = GridSpec(
        crs="EPSG:6933",
        tile_shape=XY(y=320 * multiplier, x=320 * multiplier),
        resolution=Resolution(y=-grid_res, x=grid_res),
        origin=XY(y=-7392000, x=-17376000),
    )

    # Get the tiles over Africa
    ulx, uly, lrx, lry = AFRICA_BBOX
    left, bottom, right, top = ulx, lry, lrx, uly  # (minx, miny, maxx, maxy)
    bbox = BoundingBox(left, bottom, right, top, crs="EPSG:4326").to_crs(gridspec.crs)

    tiles = list(gridspec.tiles(bbox))
    return tiles

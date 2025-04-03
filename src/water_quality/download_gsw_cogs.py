import itertools
from shapely.geometry import box
import geopandas as gpd

AFRICA_EXTENT_URL = "https://raw.githubusercontent.com/digitalearthafrica/deafrica-extent/master/africa-extent-bbox.json"


def generate_world_tiles():
    # The Global Surface Water data ara 
    # available to download in 10°x10° tiles.

    lat_range=(-60, 80)
    lon_range=(-180, 180)
    tile_size=10
    
    latitudes = range(lat_range[0], lat_range[1], tile_size)
    longitudes = range(lon_range[0], lon_range[1], tile_size)

    top_left_coords = []
    tiles_labels = []
    tiles = []
    for lat, lon in itertools.product(latitudes, longitudes):
        minx = lon
        miny = lat
        maxx = lon + tile_size
        maxy = lat + tile_size

        # Geometry of the tile from bounding box
        tile = box(minx, miny, maxx, maxy)

        # Tile label
        if abs(maxy) > abs(miny):
            y_label = f"{abs(miny)}-{abs(maxy)}N"
        else:
            y_label = f"{abs(maxy)}-{abs(miny)}S"

        if abs(maxx) > abs(minx):
            x_label = f"{abs(minx)}-{abs(maxx)}E"
        else:
            x_label = f"{abs(maxx)}-{abs(minx)}W"
        
        tile_label = f"{y_label}, {x_label}"

        # Coordinates for the topleft coorner 
        top_left = f"{abs(minx)}{"E" if minx>= 0 else "W"}_{abs(maxy)}{"N" if maxy>= 0 else "S"}"
        
        tiles.append(tile)
        tiles_labels.append(tile_label)
        top_left_coords.append(top_left)
        
    tiles_gdf = gpd.GeoDataFrame({"top_left": top_left_coords, "labels": tiles_labels, "geometry": tiles}, crs="EPSG:4326")
    return tiles_gdf


def get_africa_tiles():

    # Get all the 10°x10° tiles.
    world_tiles = generate_world_tiles()

    # Load the bounding box for Africa
    africa_extent = gpd.read_file(AFRICA_EXTENT_URL).to_crs("EPSG:4326")

    # Filter the tiles using the extent
    africa_tiles_labels = world_tiles.sjoin(
        africa_extent, predicate="intersects", how="inner"
    )["labels"].to_list()

    
    
"""
Prepare eo3 metadata for a Copernicus Global Land Service -
Lake Water Quality 2002-2012 (raster 300 m), global, 10-daily – version 1 dataset
"""

import warnings
from datetime import datetime
from itertools import chain

from eodatasets3.images import ValidDataMethod
from eodatasets3.model import DatasetDoc
from odc.apps.dc_tools._docs import odc_uuid

from water_quality.cgls_lwq.constants import MEASUREMENTS
from water_quality.cgls_lwq.netcdf import get_common_attrs, get_netcdf_subdatasets, parse_netcdf_url
from water_quality.easi_assemble import EasiPrepare


def prepare_dataset(
    dataset_path: str,
    product_yaml: str,
    output_path: str,
) -> DatasetDoc:
    """
    Prepare an eo3 metadata file for a data product.
    @param dataset_path: Path to the geotiff to create dataset metadata for.
    @param product_yaml: Path to the product definition yaml file.
    @param output_path: Path to write the output metadata file.

    :return: DatasetDoc
    """
    ## Initialise and validate inputs
    # Creates variables (see EasiPrepare for others):
    # - p.dataset_path
    # - p.product_name
    p = EasiPrepare(dataset_path, product_yaml, output_path)

    # Get information required from the dataset
    filename_prefix, acronym, date, area, sensor, version, extension = parse_netcdf_url(
        p.dataset_path
    )
    common_attrs = get_common_attrs(p.dataset_path)

    ## File format of preprocessed data
    if extension in ["nc"]:
        file_format = "NetCDF"

    ## IDs and Labels
    # The version of the source dataset
    p.dataset_version = version
    # Unique dataset UUID built from the unique Product ID and unique dataset name
    unique_name = f"{filename_prefix}_{acronym}_{date}_{area}_{sensor}_{version}"
    p.dataset_id = odc_uuid(p.product_name, p.dataset_version, [unique_name])
    # product_name is added by EasiPrepare().init()
    p.product_uri = f"https://explorer.digitalearth.africa/product/{p.product_name}"

    ## Satellite, Instrument and Processing level
    # High-level name for the source data (satellite platform or project name).
    # Comma-separated for multiple platforms.
    p.platform = common_attrs["platform"]
    #  Instrument name, optional
    p.instrument = common_attrs["sensor"]
    # Organisation that produces the data.
    # URI domain format containing a '.'
    # Plymouth Marine Laboratory and Brockmann Consult
    p.producer = "https://pml.ac.uk/, https://www.brockmann-consult.de/"
    # ODC/EASI identifier for this "family" of products, optional
    p.product_family = "cgls_water_quality"

    ## Scene capture and Processing
    # Searchable datetime of the dataset, datetime object
    p.datetime = datetime.strptime(common_attrs["time_coverage_start"], "%d-%b-%Y %H:%M:%S")
    # Searchable start and end datetimes of the dataset, datetime objects
    p.datetime_range = (
        datetime.strptime(common_attrs["time_coverage_start"], "%d-%b-%Y %H:%M:%S"),
        datetime.strptime(common_attrs["time_coverage_end"], "%d-%b-%Y %H:%M:%S"),
    )
    # When the source dataset was created by the producer, datetime object
    p.processed = datetime.fromisoformat(common_attrs["processing_time"])

    ## Geometry
    # Geometry adds a "valid data" polygon for the scene, which helps bounding box searching in ODC
    # Either provide a "valid data" polygon or calculate it from all bands in the dataset
    # ValidDataMethod.thorough = Vectorize the full valid pixel mask as-is
    # ValidDataMethod.filled = Fill holes in the valid pixel mask before vectorizing
    # ValidDataMethod.convex_hull = Take convex-hull of valid pixel mask before vectorizing
    # ValidDataMethod.bounds = Use the image file bounds, ignoring actual pixel values
    # p.geometry = Provide a "valid data" polygon rather than read from the file, shapely.geometry.base.BaseGeometry()
    # p.crs = Provide a CRS string if measurements GridSpec.crs is None, "epsg:*" or WKT
    p.valid_data_method = ValidDataMethod.bounds

    # Helpful but not critical
    p.properties["odc:file_format"] = file_format
    p.properties["odc:product"] = p.product_name

    ## Ignore warnings, OPTIONAL
    # Ignore unknown property warnings (generated in eodatasets3.properties.Eo3Dict().normalise_and_set())
    # Eodatasets3 validates properties against a hardcoded list, which includes DEA stuff so no harm if we add our own
    custom_prefix = "cgls_lwq"  # usually related to the product name or type
    warnings.filterwarnings("ignore", message=f".*Unknown stac property.+{custom_prefix}:.+")
    ## Product-specific properties, OPTIONAL
    # For examples see eodatasets3.properties.Eo3Dict().KNOWN_PROPERTIES
    p.properties[f"{custom_prefix}:processing_centre"] = common_attrs["processing_centre"]
    p.properties[f"{custom_prefix}:processing_level"] = common_attrs["processing_level"]
    p.properties[f"{custom_prefix}:processor"] = common_attrs["processor"]
    p.properties[f"{custom_prefix}:product_type"] = common_attrs["product_type"]
    p.properties[f"{custom_prefix}:title"] = common_attrs["title"]
    p.properties[f"{custom_prefix}:trackingid"] = common_attrs["trackingID"]

    # Check all the measurements of interest are defined in the product file
    assert set(MEASUREMENTS).issubset(set(chain.from_iterable(p.get_product_measurements())))
    # Check all the measurements of interest are in the dataset file
    assert set(MEASUREMENTS).issubset(set(get_netcdf_subdatasets(p.dataset_path)))

    # Add measurement paths
    for measurment in MEASUREMENTS:
        p.note_measurement(
            measurement_name=measurment,
            file_path=p.dataset_path,
            layer=measurment,
            expand_valid_data=True,
            relative_to_metadata=False,
        )
    return p.to_dataset_doc(validate_correctness=True, sort_measurements=True)

from eodatasets3.model import DatasetDoc

from water_quality.easi_assemble import EasiPrepare


def prepare_dataset(
    dataset_path: str,
    product_yaml: str,
    output_path: str,
) -> DatasetDoc:
    """
    Prepare an eo3 metadata file for SAMPLE data product.
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

"""
Manifest files and measurements of interest for the
Copernicus Global Land Service - Lake Water Quality ODC products
"""

AFRICA_EXTENT_URL = "https://raw.githubusercontent.com/digitalearthafrica/deafrica-extent/master/africa-extent-bbox.json"

MANIFEST_FILE_URLS = {
    "cgls_lwq300_2002_2012": "https://globalland.vito.be/download/manifest/lwq_300m_v1_10daily-reproc_netcdf/manifest_clms_global_lwq_300m_v1_10daily-reproc_netcdf_latest.txt"
}
MEASUREMENTS = [
    "num_obs",
    "first_obs",
    "trophic_state_index",
    "last_obs",
    "n_obs_quality_risk_sum",
    "stats_valid_obs_tsi_sum",
    "stats_valid_obs_turbidity_sum",
    "turbidity_mean",
    "turbidity_sigma",
]

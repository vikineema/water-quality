"""
Manifest files and measurements of interest for the
Copernicus Global Land Service - Lake Water Quality ODC products
"""

AFRICA_BBOX = [-26.36, 38.35, 64.50, -47.97]
AFRICA_EXTENT_URL = "https://raw.githubusercontent.com/digitalearthafrica/deafrica-extent/master/africa-extent-bbox.json"

MANIFEST_FILE_URLS = {
    "cgls_lwq300_2002_2012": "https://globalland.vito.be/download/manifest/lwq_300m_v1_10daily-reproc_netcdf/manifest_clms_global_lwq_300m_v1_10daily-reproc_netcdf_latest.txt",
    "cgls_lwq300_2016_2024": "https://globalland.vito.be/download/manifest/lwq_300m_v1_10daily-nrt_netcdf/manifest_clms_global_lwq_300m_v1_10daily-nrt_netcdf_latest.txt",
    "cgls_lwq100_2019_2024": "https://globalland.vito.be/download/manifest/lwq_100m_v1_10daily-nrt_netcdf/manifest_clms_global_lwq_100m_v1_10daily-nrt_netcdf_latest.txt",
    "cgls_lwq300_2024_nrt": "https://globalland.vito.be/download/manifest/lwq_300m_v2_10daily-nrt_netcdf/manifest_clms_global_lwq_300m_v2_10daily-nrt_netcdf_latest.txt",
    "cgls_lwq100_2024_nrt": "https://globalland.vito.be/download/manifest/lwq_100m_v2_10daily-nrt_netcdf/manifest_clms_global_lwq_100m_v2_10daily-nrt_netcdf_latest.txt",
}
MEASUREMENTS_1 = [
    "first_obs",
    "last_obs",
    "n_obs_quality_risk_sum",
    "num_obs",
    "stats_valid_obs_tsi_sum",
    "stats_valid_obs_turbidity_sum",
    "trophic_state_index",
    "turbidity_mean",
    "turbidity_sigma",
]
MEASUREMENTS = {"cgls_lwq300_2002_2012": MEASUREMENTS_1, "cgls_lwq300_2016_2024": MEASUREMENTS_1}
NAMING_PREFIX = "c_gls"

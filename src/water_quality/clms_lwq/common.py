# map product name to manifest file url
MANIFEST_FILE_URLS = {
    "cgls_LWQ300_v1_300": "https://globalland.vito.be/download/manifest/lwq_300m_v1_10daily-reproc_netcdf/manifest_clms_global_lwq_300m_v1_10daily-reproc_netcdf_latest.txt"
}
# Bands in the netcdf file to check
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

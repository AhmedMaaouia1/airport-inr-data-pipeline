from src.geo.load_airport import load_airport_features
from src.geo.normalize_geometry import clean_and_normalize_geometries
from src.geo.building_height import estimate_building_height
from src.core.config import load_config
from src.core.logging import setup_logger

logger = setup_logger()
config = load_config()

DB_PATH      = config["airport"]["database_path"]
DEF_HEIGHT   = config["airport"]["default_building_height"]
OUTPUT_PATH  = config["paths"]["staging_buildings"]

logger.info("=" * 60)
logger.info("STAGE 1: LOADING AIRPORT FEATURES")
logger.info("=" * 60)

logger.info("Loading all airport features from %s...", DB_PATH)
gdf = load_airport_features(DB_PATH)
logger.info("Total features loaded: %d", len(gdf))

# Ensure height column exists
if "height" not in gdf.columns:
    gdf["height"] = None

logger.info("\nCleaning and normalizing geometries...")
gdf = clean_and_normalize_geometries(gdf)
logger.info("Total polygons after normalization: %d", len(gdf))

# Estimate heights only for buildings
logger.info("\nEstimating heights for buildings...")
buildings_mask = gdf["feature_type"] == "building"
if buildings_mask.any():
    buildings_gdf = gdf[buildings_mask].copy()
    buildings_gdf_with_heights = estimate_building_height(
        buildings_gdf,
        default_height=DEF_HEIGHT
    )
    gdf.loc[buildings_mask, "height"] = buildings_gdf_with_heights["height"]
    logger.info("Building heights estimated: %d buildings", buildings_mask.sum())
else:
    logger.info("No buildings in dataset")

logger.info("\nBounding box: %s", gdf.total_bounds)

logger.info("\nFeature distribution:")
for ftype, count in sorted(gdf["feature_type"].value_counts().items()):
    logger.info("  - %s: %d", ftype, count)

logger.info("\nExporting features to staging: %s", OUTPUT_PATH)
gdf.to_parquet(OUTPUT_PATH)
logger.info("Features exported successfully!")
logger.info("=" * 60)
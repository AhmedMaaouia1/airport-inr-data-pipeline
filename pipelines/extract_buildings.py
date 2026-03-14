from src.geo.load_airport import load_buildings
from src.geo.clean_geometries import clean_buildings
from src.geo.building_height import estimate_building_height
from src.core.config import load_config
from src.core.logging import setup_logger

logger = setup_logger()
config = load_config()

DB_PATH      = config["airport"]["database_path"]
DEF_HEIGHT   = config["airport"]["default_building_height"]
OUTPUT_PATH  = config["paths"]["staging_buildings"]

logger.info("Chargement des bâtiments depuis %s...", DB_PATH)
gdf = load_buildings(DB_PATH)
logger.info("Bâtiments chargés : %d", len(gdf))

logger.info("Nettoyage des géométries...")
gdf = clean_buildings(gdf)

logger.info("Estimation des hauteurs...")
gdf = estimate_building_height(gdf, default_height=DEF_HEIGHT)

logger.info("Bounding box : %s", gdf.total_bounds)

logger.info("Export des bâtiments vers staging : %s", OUTPUT_PATH)
gdf.to_parquet(OUTPUT_PATH)
logger.info("Bâtiments exportés : %s", OUTPUT_PATH)
import geopandas as gpd
import os

from src.mesh.extrude_buildings import extrude_features
from src.mesh.merge_meshes import merge_meshes
from src.core.config import load_config
from src.core.logging import setup_logger

logger = setup_logger()
config = load_config()

INPUT_PATH  = config["paths"]["staging_buildings"]
AIRPORT_CODE = config["airport"]["code"]
PROCESSED_ROOT = config["paths"]["processed_root"]
HEIGHTS_CONFIG = config["features"]["extrusion_heights"]

OUTPUT_DIR = os.path.join(PROCESSED_ROOT, AIRPORT_CODE)
os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_PATH = os.path.join(OUTPUT_DIR, f"{AIRPORT_CODE}_mesh.obj")

logger.info("=" * 60)
logger.info("STAGE 2: BUILDING 3D MESH")
logger.info("=" * 60)

logger.info("Loading staged features from %s...", INPUT_PATH)
gdf = gpd.read_parquet(INPUT_PATH)
logger.info("Features loaded: %d", len(gdf))
logger.info("Airport code      : %s", AIRPORT_CODE)
logger.info("Output directory  : %s", OUTPUT_DIR)

logger.info("\nFeature distribution before extrusion:")
for ftype, count in sorted(gdf["feature_type"].value_counts().items()):
    logger.info("  - %s: %d", ftype, count)

logger.info("\nExtruding features...")
meshes = extrude_features(gdf, HEIGHTS_CONFIG)
logger.info("Number of meshes generated: %d", len(meshes))

logger.info("\nMerging meshes...")
airport_mesh = merge_meshes(meshes)

logger.info("Mesh statistics:")
logger.info("  Vertices: %d", len(airport_mesh.vertices))
logger.info("  Faces    : %d", len(airport_mesh.faces))
logger.info("  Watertight: %s", airport_mesh.is_watertight)
logger.info("  Split components: %d", len(airport_mesh.split()))

logger.info("\nFixing normals...")
if not airport_mesh.is_watertight:
    airport_mesh.fix_normals()
    logger.info("Normals fixed")

logger.info("\nExporting mesh to %s...", OUTPUT_PATH)
airport_mesh.export(OUTPUT_PATH)
logger.info("✓ Mesh exported successfully!")
logger.info("=" * 60)
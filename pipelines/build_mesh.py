import geopandas as gpd
import os

from src.mesh.extrude_buildings import extrude_buildings
from src.mesh.merge_meshes import merge_meshes
from src.core.config import load_config
from src.core.logging import setup_logger

logger = setup_logger()
config = load_config()

INPUT_PATH  = config["paths"]["staging_buildings"]
AIRPORT_CODE = config["airport"]["code"]
PROCESSED_ROOT = config["paths"]["processed_root"]

OUTPUT_DIR = os.path.join(PROCESSED_ROOT, AIRPORT_CODE)
os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_PATH = os.path.join(OUTPUT_DIR, f"{AIRPORT_CODE}_mesh.obj")

logger.info("Chargement des bâtiments depuis %s...", INPUT_PATH)
gdf = gpd.read_parquet(INPUT_PATH)
logger.info("Bâtiments chargés : %d", len(gdf))
logger.info("Airport code      : %s", AIRPORT_CODE)
logger.info("Output directory  : %s", OUTPUT_DIR)

logger.info("Extrusion des bâtiments...")
meshes = extrude_buildings(gdf)
logger.info("Nombre de meshes générés : %d", len(meshes))

airport_mesh = merge_meshes(meshes)

logger.info("Vertices : %d", len(airport_mesh.vertices))
logger.info("Faces    : %d", len(airport_mesh.faces))

logger.info("Vérification du mesh...")
logger.info("Watertight         : %s", airport_mesh.is_watertight)
logger.info("Nombre de composantes : %d", len(airport_mesh.split()))

airport_mesh.export(OUTPUT_PATH)
logger.info("Mesh exporté : %s", OUTPUT_PATH)
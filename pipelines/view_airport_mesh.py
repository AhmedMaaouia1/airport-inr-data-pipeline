import geopandas as gpd

from src.mesh.extrude_buildings import extrude_buildings
from src.mesh.merge_meshes import merge_meshes
from src.visualization.mesh_viewer import show_mesh
from src.core.logging import setup_logger

logger = setup_logger()


logger.info("Chargement bâtiments...")
gdf = gpd.read_parquet("data/staging/buildings.parquet")

logger.info("Extrusion...")
meshes = extrude_buildings(gdf)

logger.info("Fusion...")
airport_mesh = merge_meshes(meshes)

logger.info("Affichage du mesh...")
show_mesh(airport_mesh)
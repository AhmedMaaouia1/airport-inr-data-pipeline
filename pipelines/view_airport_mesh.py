import geopandas as gpd

from src.mesh.extrude_buildings import extrude_buildings
from src.mesh.merge_meshes import merge_meshes
from src.visualization.mesh_viewer import show_mesh


print("Chargement bâtiments...")
gdf = gpd.read_parquet("data/staging/buildings.parquet")

print("Extrusion...")
meshes = extrude_buildings(gdf)

print("Fusion...")
airport_mesh = merge_meshes(meshes)

print("Affichage du mesh...")
show_mesh(airport_mesh)
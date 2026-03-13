from src.geo.load_airport import load_buildings
from src.mesh.extrude_buildings import extrude_buildings
from src.mesh.merge_meshes import merge_meshes

DB_PATH = "data/raw/openalaqs/LFPO_Project.sqlite"

print("Chargement des bâtiments...")
gdf = load_buildings(DB_PATH)

print("Extrusion des bâtiments...")
meshes = extrude_buildings(gdf)

print("Nombre de meshes générés :", len(meshes))

airport_mesh = merge_meshes(meshes)

print("Vertices :", len(airport_mesh.vertices))
print("Faces :", len(airport_mesh.faces))

airport_mesh.export("data/processed/orly_mesh.obj")

print("Mesh exporté : data/processed/orly_mesh.obj")
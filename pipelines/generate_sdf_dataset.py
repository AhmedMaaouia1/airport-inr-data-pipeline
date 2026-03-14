from src.geo.load_airport import load_buildings
from src.mesh.extrude_buildings import extrude_buildings
from src.mesh.merge_meshes import merge_meshes

from src.sdf.sample_surface import sample_surface
from src.sdf.sample_near_surface import sample_near_surface
from src.sdf.sample_free_space import sample_free_space
from src.sdf.compute_sdf_chunked import compute_sdf_chunked

from src.core.normalize_coordinates import normalize_points

import numpy as np
import pandas as pd


DB_PATH = "data/raw/openalaqs/LFPO_Project.sqlite"


print("Chargement des bâtiments...")
gdf = load_buildings(DB_PATH)


print("Création des meshes...")
meshes = extrude_buildings(gdf)

airport_mesh = merge_meshes(meshes)


print("Calcul bounding box...")
bounds = gdf.total_bounds


print("Sampling surface...")
surface_points = sample_surface(airport_mesh, 20000)


print("Sampling near surface...")
near_surface_points = sample_near_surface(surface_points)


print("Sampling free space...")
free_space_points = sample_free_space(bounds, 20000)


points = np.vstack((
    surface_points,
    near_surface_points,
    free_space_points
))


print("Calcul SDF...")

distances = compute_sdf_chunked(
    airport_mesh,
    points,
    chunk_size=5000
)


print("Normalisation des coordonnées...")

points_normalized, center, scale = normalize_points(points)

distances_normalized = distances / scale


dataset = np.hstack((
    points_normalized,
    distances_normalized.reshape(-1, 1)
))


df = pd.DataFrame(
    dataset,
    columns=["x", "y", "z", "s"]
)


print(df.head())
print("Dataset size :", len(df))


df.to_parquet(
    "data/processed/orly_sdf_dataset.parquet",
    index=False
)


print("Dataset sauvegardé")

print("Center :", center)
print("Scale :", scale)


# Export du nuage de points pour visualisation

ply_path = "data/processed/orly_sdf_points.ply"

with open(ply_path, "w") as f:

    f.write("ply\n")
    f.write("format ascii 1.0\n")
    f.write(f"element vertex {len(points_normalized)}\n")
    f.write("property float x\n")
    f.write("property float y\n")
    f.write("property float z\n")
    f.write("end_header\n")

    for p in points_normalized:
        f.write(f"{p[0]} {p[1]} {p[2]}\n")


print("Nuage de points exporté :", ply_path)
from src.geo.load_airport import load_buildings
from src.mesh.extrude_buildings import extrude_buildings
from src.mesh.merge_meshes import merge_meshes
from src.sdf.sample_points import sample_points
from src.sdf.compute_sdf import compute_sdf

import numpy as np
import pandas as pd


DB_PATH = "data/raw/openalaqs/LFPO_Project.sqlite"

print("Chargement des bâtiments...")
gdf = load_buildings(DB_PATH)

print("Création des meshes...")
meshes = extrude_buildings(gdf)

airport_mesh = merge_meshes(meshes)

print("Sampling des points...")

bounds = gdf.total_bounds

points = sample_points(bounds, n_points=20000)

print("Calcul SDF...")

distances = compute_sdf(airport_mesh, points)

dataset = np.hstack((points, distances.reshape(-1,1)))

df = pd.DataFrame(dataset, columns=["x","y","z","s"])

print(df.head())
print("Dataset size :", len(df))

df.to_parquet(
    "data/processed/orly_sdf_dataset.parquet",
    index=False
)

print("Dataset sauvegardé")
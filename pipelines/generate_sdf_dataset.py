from src.geo.load_airport import load_buildings
from src.mesh.extrude_buildings import extrude_buildings
from src.mesh.merge_meshes import merge_meshes

from src.sdf.sample_surface import sample_surface
from src.sdf.sample_near_surface import sample_near_surface
from src.sdf.sample_free_space import sample_free_space
from src.sdf.compute_sdf_chunked import compute_sdf_chunked

from src.core.normalize_coordinates import normalize_points
from src.core.config import load_config
from src.validation.check_dataset import validate_sdf_dataset

import numpy as np
import pandas as pd
import os
from sklearn.model_selection import train_test_split

from src.core.logging import setup_logger

logger = setup_logger()
config = load_config()

DB_PATH    = config["airport"]["database_path"]
AIRPORT_CODE = config["airport"]["code"]
PATHS      = config["paths"]
TRAIN_SPLIT = config["dataset"]["train_split"]

OUTPUT_DIR = os.path.join(PATHS["processed_root"], AIRPORT_CODE)
os.makedirs(OUTPUT_DIR, exist_ok=True)

TRAIN_PATH = os.path.join(OUTPUT_DIR, f"{AIRPORT_CODE}_sdf_train.parquet")
VAL_PATH = os.path.join(OUTPUT_DIR, f"{AIRPORT_CODE}_sdf_val.parquet")
PLY_PATH = os.path.join(OUTPUT_DIR, f"{AIRPORT_CODE}_sdf_points.ply")


logger.info("Chargement des bâtiments...")
gdf = load_buildings(DB_PATH)
logger.info("Airport code      : %s", AIRPORT_CODE)
logger.info("Output directory  : %s", OUTPUT_DIR)


logger.info("Création des meshes...")
meshes = extrude_buildings(gdf)

airport_mesh = merge_meshes(meshes)


logger.info("Calcul bounding box...")
bounds = gdf.total_bounds


logger.info("Sampling surface...")
surface_points = sample_surface(
    airport_mesh,
    config["sampling"]["surface_points"]
)


logger.info("Sampling near surface...")
near_surface_points = sample_near_surface(
    surface_points,
    sigma=config["sampling"]["near_surface_noise"]
)


logger.info("Sampling free space...")
free_space_points = sample_free_space(
    bounds,
    config["sampling"]["free_space_points"]
)


points = np.vstack((
    surface_points,
    near_surface_points,
    free_space_points
))


logger.info("Calcul SDF...")
distances = compute_sdf_chunked(
    airport_mesh,
    points,
    chunk_size=config["sdf"]["chunk_size"]
)


logger.info("Normalisation des coordonnées...")
points_normalized, center, scale = normalize_points(points)
distances_normalized = distances / scale


dataset = np.hstack((
    points_normalized,
    distances_normalized.reshape(-1, 1)
))


df = pd.DataFrame(dataset, columns=["x", "y", "z", "s"])

logger.info(df.head())
logger.info("Dataset size : %d", len(df))


# Validation du dataset
validate_sdf_dataset(df)


# Split train / validation
train_df, val_df = train_test_split(
    df,
    test_size=1 - TRAIN_SPLIT,
    random_state=42
)

logger.info("Train size      : %d", len(train_df))
logger.info("Validation size : %d", len(val_df))

train_df.to_parquet(TRAIN_PATH, index=False)
val_df.to_parquet(VAL_PATH,   index=False)

logger.info("Datasets sauvegardés")
logger.info("Center : %s", center)
logger.info("Scale  : %s", scale)


# Export du nuage de points pour visualisation
ply_path = PLY_PATH

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


logger.info("Nuage de points exporté : %s", ply_path)
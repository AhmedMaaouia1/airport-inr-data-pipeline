import geopandas as gpd
import numpy as np
import pandas as pd
import os
import json
from sklearn.model_selection import train_test_split

from src.mesh.extrude_buildings import extrude_features
from src.mesh.merge_meshes import merge_meshes

from src.sdf.sample_surface import sample_surface
from src.sdf.sample_near_surface import sample_near_surface
from src.sdf.sample_free_space import sample_free_space
from src.sdf.compute_sdf_chunked import compute_sdf_chunked

from src.core.normalize_coordinates import normalize_points_separate
from src.core.config import load_config
from src.validation.check_dataset import validate_sdf_dataset

from src.core.logging import setup_logger

logger = setup_logger()
config = load_config()

INPUT_PATH = config["paths"]["staging_buildings"]
AIRPORT_CODE = config["airport"]["code"]
PATHS      = config["paths"]
TRAIN_SPLIT = config["dataset"]["train_split"]
HEIGHTS_CONFIG = config["features"]["extrusion_heights"]

OUTPUT_DIR = os.path.join(PATHS["processed_root"], AIRPORT_CODE)
os.makedirs(OUTPUT_DIR, exist_ok=True)

TRAIN_PATH = os.path.join(OUTPUT_DIR, f"{AIRPORT_CODE}_sdf_train.parquet")
VAL_PATH = os.path.join(OUTPUT_DIR, f"{AIRPORT_CODE}_sdf_val.parquet")
PLY_PATH = os.path.join(OUTPUT_DIR, f"{AIRPORT_CODE}_sdf_points.ply")

logger.info("=" * 60)
logger.info("STAGE 3: GENERATING SDF DATASET")
logger.info("=" * 60)

logger.info("Loading staged features from %s...", INPUT_PATH)
gdf = gpd.read_parquet(INPUT_PATH)
logger.info("Features loaded: %d", len(gdf))
logger.info("Airport code    : %s", AIRPORT_CODE)
logger.info("Output directory: %s", OUTPUT_DIR)

logger.info("\nFeature distribution:")
for ftype, count in sorted(gdf["feature_type"].value_counts().items()):
    logger.info("  - %s: %d", ftype, count)

logger.info("\nCreating 3D mesh from all features...")
meshes = extrude_features(gdf, HEIGHTS_CONFIG)
airport_mesh = merge_meshes(meshes)

logger.info("Mesh statistics:")
logger.info("  Vertices: %d", len(airport_mesh.vertices))
logger.info("  Faces: %d", len(airport_mesh.faces))
logger.info("  Watertight: %s", airport_mesh.is_watertight)

logger.info("\nCalculating bounding box...")
bounds = gdf.total_bounds
logger.info("Bounds: %s", bounds)

logger.info("\nSampling surface points...")
surface_points = sample_surface(
    airport_mesh,
    config["sampling"]["surface_points"]
)
logger.info("Surface points sampled: %d", len(surface_points))

logger.info("Sampling near-surface points...")
near_surface_points = sample_near_surface(
    surface_points,
    sigma=config["sampling"]["near_surface_noise"]
)
logger.info("Near-surface points sampled: %d", len(near_surface_points))

logger.info("Sampling free-space points...")
free_space_points = sample_free_space(
    bounds,
    config["sampling"]["free_space_points"]
)
logger.info("Free-space points sampled: %d", len(free_space_points))

# Combine all point samples
points = np.vstack((
    surface_points,
    near_surface_points,
    free_space_points
))
logger.info("Total points: %d", len(points))

logger.info("\nComputing SDF values...")
distances = compute_sdf_chunked(
    airport_mesh,
    points,
    chunk_size=config["sdf"]["chunk_size"]
)

logger.info("\nNormalizing coordinates...")
points_normalized, centers, scales = normalize_points_separate(points)

# Normalize distances using XY scale (lateral distances dominate in airport geometry)
distances_normalized = distances / scales['xy']

logger.info("Normalization - XY scale:  %.4f", scales['xy'])
logger.info("Normalization - Z scale:   %.4f", scales['z'])
logger.info("Normalization - XY center: [%.2f, %.2f]", centers['xy'][0], centers['xy'][1])
logger.info("Normalization - Z center:  %.2f", centers['z'])

# Create dataset
dataset = np.hstack((
    points_normalized,
    distances_normalized.reshape(-1, 1)
))

df = pd.DataFrame(dataset, columns=["x", "y", "z", "s"])

logger.info("\nDataset preview:")
logger.info(df.head())
logger.info("Dataset size: %d", len(df))

# Validate dataset
logger.info("\nValidating dataset...")
validate_sdf_dataset(df)

# Split train / validation
logger.info("\nSplitting dataset...")
train_df, val_df = train_test_split(
    df,
    test_size=1 - TRAIN_SPLIT,
    random_state=42
)

logger.info("Train set size: %d", len(train_df))
logger.info("Validation set size: %d", len(val_df))

# Export datasets
logger.info("\nExporting datasets...")
train_df.to_parquet(TRAIN_PATH, index=False)
val_df.to_parquet(VAL_PATH, index=False)
logger.info("✓ Train dataset: %s", TRAIN_PATH)
logger.info("✓ Validation dataset: %s", VAL_PATH)

# Export point cloud for visualization
logger.info("\nExporting point cloud...")
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

logger.info("✓ Point cloud: %s", ply_path)

# Save normalization metadata for inference
logger.info("\nSaving normalization metadata...")
metadata_path = os.path.join(OUTPUT_DIR, f"{AIRPORT_CODE}_normalization_metadata.json")
metadata = {
    "normalization_type": "separate_xy_z",
    "centers": {
        "xy": centers['xy'].tolist(),
        "z": float(centers['z'])
    },
    "scales": {
        "xy": float(scales['xy']),
        "z": float(scales['z'])
    },
    "description": "Use to denormalize predictions during inference. See normalize_coordinates.py docstring.",
    "denormalization_formula": {
        "xy": "points_original[:, :2] = (points_normalized[:, :2] * scales['xy']) + centers['xy']",
        "z": "points_original[:, 2] = (points_normalized[:, 2] * scales['z']) + centers['z']",
        "sdf": "sdf_original = sdf_normalized * scales['xy']"
    }
}

with open(metadata_path, 'w') as f:
    json.dump(metadata, f, indent=2)

logger.info("✓ Normalization metadata: %s", metadata_path)
logger.info("=" * 60)
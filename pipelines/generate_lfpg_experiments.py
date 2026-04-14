import os
import yaml
import numpy as np
import pandas as pd
import geopandas as gpd
import trimesh
import json
from sklearn.model_selection import train_test_split
from src.mesh.extrude_buildings import extrude_features
from src.mesh.merge_meshes import merge_meshes
from src.sdf.sample_surface import sample_surface
from src.sdf.sample_near_surface import sample_near_surface
from src.sdf.sample_free_space import sample_free_space
from src.sdf.compute_sdf_chunked import compute_sdf_chunked
from src.core.normalize_coordinates import normalize_points
from src.validation.check_dataset import validate_sdf_dataset
from src.core.logging import setup_logger

logger = setup_logger()

EXPERIMENT_CONFIG = "experiments/lfpg_sampling_experiments.yaml"
DB_PATH = "data/raw/openalaqs/LFPG_gates_final.sqlite"
AIRPORT_CODE = "LFPG"
CRS = "EPSG:4326"

# Load experiment configs
def load_experiment_configs():
    with open(EXPERIMENT_CONFIG, "r") as f:
        yml = yaml.safe_load(f)
    return yml["lfpg_experiments"]

# Load gates (instead of buildings)
def load_gates(db_path):
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.enable_load_extension(True)
    conn.load_extension("mod_spatialite")
    query = """
    SELECT oid, gate_id AS feature_id, AsBinary(geometry) AS geometry
    FROM shapes_gates WHERE geometry IS NOT NULL
    """
    df = pd.read_sql(query, conn)
    gdf = gpd.GeoDataFrame(df, geometry=gpd.GeoSeries.from_wkb(df["geometry"]), crs=CRS)
    conn.close()
    gdf["feature_type"] = "gate"
    return gdf

def main():
    configs = load_experiment_configs()
    logger.info(f"Loaded {len(configs)} experiment configs.")

    # Load gates and create mesh once
    logger.info(f"Loading gates from {DB_PATH} ...")
    gdf = load_gates(DB_PATH)
    logger.info(f"Gates loaded: {len(gdf)}")
    logger.info("Extruding mesh...")
    meshes = extrude_features(gdf, {"gate": 0.02})
    airport_mesh = merge_meshes(meshes)
    logger.info(f"Mesh: {len(airport_mesh.vertices)} vertices, {len(airport_mesh.faces)} faces, watertight={airport_mesh.is_watertight}")

    # Sample surface points (max needed)
    max_points = max([cfg["near_surface_points"] + cfg["mid_surface_points"] for cfg in configs])
    logger.info(f"Sampling {max_points} surface points (for all configs)...")
    surface_points = sample_surface(airport_mesh, max_points)

    for cfg in configs:
        name = cfg["name"]
        out_dir = os.path.join("data/processed", name)
        os.makedirs(out_dir, exist_ok=True)
        logger.info(f"\n=== Generating dataset: {name} ===")
        logger.info(f"Config: {cfg}")

        # 1. Free space
        bounds = gdf.total_bounds
        free_space_points = sample_free_space(bounds, cfg["free_space_points"])

        # 2. Near-surface (très proche)
        near_points = surface_points[:cfg["near_surface_points"]]
        near_surface_points = sample_near_surface(near_points, sigma=cfg["near_surface_sigma"])

        # 3. Near-surface (moyennement proche)
        mid_points = surface_points[cfg["near_surface_points"]:cfg["near_surface_points"]+cfg["mid_surface_points"]]
        mid_surface_points = sample_near_surface(mid_points, sigma=cfg["mid_surface_sigma"])

        # Stack all
        all_points = np.vstack((near_surface_points, mid_surface_points, free_space_points))
        logger.info(f"Total points: {len(all_points)}")

        # Compute SDF
        logger.info("Computing SDF values...")
        distances = compute_sdf_chunked(airport_mesh, all_points, chunk_size=5000)

        # Normalize
        logger.info("Normalizing coordinates...")
        points_normalized, center, scale = normalize_points(all_points)
        distances_normalized = distances / scale

        # Save dataset
        dataset = np.hstack((points_normalized, distances_normalized.reshape(-1, 1)))
        df = pd.DataFrame(dataset, columns=["x", "y", "z", "s"])
        logger.info(df.head())
        logger.info(f"Dataset size: {len(df)}")
        validate_sdf_dataset(df)

        # Split train / validation (90% / 10%)
        logger.info("Splitting train/validation...")
        train_df, val_df = train_test_split(df, test_size=0.1, random_state=42)
        logger.info(f"Train set size: {len(train_df)}")
        logger.info(f"Validation set size: {len(val_df)}")

        # Save parquet files
        train_path = os.path.join(out_dir, f"{name}_sdf_train.parquet")
        val_path = os.path.join(out_dir, f"{name}_sdf_val.parquet")
        train_df.to_parquet(train_path, index=False)
        val_df.to_parquet(val_path, index=False)
        logger.info(f"✓ Train: {train_path}")
        logger.info(f"✓ Validation: {val_path}")

        # Save normalization metadata
        metadata = {
            "normalization_type": "unified",
            "center": center.tolist(),
            "scale": float(scale),
            "description": "Use to denormalize predictions during inference.",
            "denormalization_formula": {
                "xyz": "points_original = (points_normalized * scale) + center",
                "sdf": "sdf_original = sdf_normalized * scale"
            }
        }
        meta_path = os.path.join(out_dir, f"{name}_normalization_metadata.json")
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"✓ Metadata: {meta_path}")

        # Save point cloud (PLY)
        ply_path = os.path.join(out_dir, f"{name}_points.ply")
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
        logger.info(f"✓ PLY: {ply_path}")

if __name__ == "__main__":
    main()

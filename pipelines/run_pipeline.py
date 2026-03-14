import subprocess
import sys
import time
import pandas as pd
import os

from src.core.config import load_config
from src.core.logging import setup_logger

logger = setup_logger()
config = load_config()

AIRPORT_CODE = config["airport"]["code"]
PATHS = config["paths"]
OUTPUT_DIR = os.path.join(PATHS["processed_root"], AIRPORT_CODE)


def get_output_paths() -> dict:
    return {
        "staging_buildings": PATHS["staging_buildings"],
        "processed_mesh": os.path.join(OUTPUT_DIR, f"{AIRPORT_CODE}_mesh.obj"),
        "sdf_train": os.path.join(OUTPUT_DIR, f"{AIRPORT_CODE}_sdf_train.parquet"),
        "sdf_val": os.path.join(OUTPUT_DIR, f"{AIRPORT_CODE}_sdf_val.parquet"),
        "sdf_points_ply": os.path.join(OUTPUT_DIR, f"{AIRPORT_CODE}_sdf_points.ply"),
    }


def run_step(script_name: str) -> float:
    """Lance une étape de la pipeline et retourne le temps écoulé en secondes."""
    logger.info("\n===== Running %s =====", script_name)
    start = time.time()

    result = subprocess.run(
        ["python", f"pipelines/{script_name}"],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    elapsed = time.time() - start

    if result.returncode != 0:
        logger.error("XX Erreur lors de l'exécution de %s", script_name)
        sys.exit(1)

    logger.info("--> %s terminé en %.1f s", script_name, elapsed)
    return elapsed


def print_summary(timings: dict) -> None:
    """Affiche le résumé final de la pipeline."""
    paths = get_output_paths()

    logger.info("\n" + "=" * 60)
    logger.info("  RÉSUMÉ DE LA PIPELINE")
    logger.info("=" * 60)

    # Temps par étape
    total_time = sum(timings.values())
    for step, elapsed in timings.items():
        logger.info("  %-35s %.1f s", step, elapsed)
    logger.info("  %-35s %.1f s", "TOTAL", total_time)

    # Tailles des datasets
    try:
        train_df = pd.read_parquet(paths["sdf_train"])
        val_df   = pd.read_parquet(paths["sdf_val"])
        logger.info("")
        logger.info("  Dataset total  : %d points", len(train_df) + len(val_df))
        logger.info("  Train          : %d points", len(train_df))
        logger.info("  Validation     : %d points", len(val_df))
        logger.info("  Split          : %.0f%% / %.0f%%",
                    100 * len(train_df) / (len(train_df) + len(val_df)),
                    100 * len(val_df)   / (len(train_df) + len(val_df)))
    except FileNotFoundError:
        logger.warning("  Les fichiers Parquet ne sont pas encore disponibles.")

    logger.info("=" * 60)
    logger.info("  Fichiers générés :")
    logger.info("    - %s", paths["staging_buildings"])
    logger.info("    - %s", paths["processed_mesh"])
    logger.info("    - %s", paths["sdf_train"])
    logger.info("    - %s", paths["sdf_val"])
    logger.info("    - %s", paths["sdf_points_ply"])
    logger.info("=" * 60 + "\n")


def main():
    logger.info("\nStarting Airport INR Data Pipeline\n")
    logger.info("Running pipeline for airport: %s", AIRPORT_CODE)
    logger.info("Staging buildings path: %s", PATHS["staging_buildings"])
    logger.info("Output directory: %s", OUTPUT_DIR)

    output_paths = get_output_paths()
    logger.info("Generated output paths:")
    logger.info("  - %s", output_paths["processed_mesh"])
    logger.info("  - %s", output_paths["sdf_train"])
    logger.info("  - %s", output_paths["sdf_val"])
    logger.info("  - %s", output_paths["sdf_points_ply"])
    timings = {}

    timings["extract_buildings.py"]    = run_step("extract_buildings.py")
    timings["build_mesh.py"]           = run_step("build_mesh.py")
    timings["generate_sdf_dataset.py"] = run_step("generate_sdf_dataset.py")

    logger.info("\n---> Pipeline completed successfully")
    print_summary(timings)


if __name__ == "__main__":
    main()
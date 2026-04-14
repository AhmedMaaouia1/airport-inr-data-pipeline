#!/usr/bin/env python3
"""
Complete pipeline runner for airport INR dataset generation.

Usage:
    python -m pipelines.run_pipeline                  # Use LFPO from config
    python -m pipelines.run_pipeline --airport LFPG   # Specify airport code
"""

import sys
import argparse
import logging
from pathlib import Path
import os
import time

from src.core.logging import setup_logger
from src.core.config import load_config

logger = setup_logger()


def get_output_paths(airport_code: str) -> dict:
    """Get output paths for the airport."""
    config = load_config()
    output_dir = os.path.join(config["paths"]["processed_root"], airport_code)
    return {
        "staging_buildings": config["paths"]["staging_buildings"],
        "processed_mesh": os.path.join(output_dir, f"{airport_code}_mesh.obj"),
        "sdf_train": os.path.join(output_dir, f"{airport_code}_sdf_train.parquet"),
        "sdf_val": os.path.join(output_dir, f"{airport_code}_sdf_val.parquet"),
        "sdf_points_ply": os.path.join(output_dir, f"{airport_code}_sdf_points.ply"),
    }


def run_stages(airport_code: str | None = None) -> None:
    """Run all pipeline stages."""
    
    # Load config
    config = load_config()
    
    if airport_code:
        config["airport"]["code"] = airport_code
        # Build database path from airport code
        db_path = f"data/raw/openalaqs/{airport_code}.sqlite"
        config["airport"]["database_path"] = db_path
    
    airport = config["airport"]["code"]
    db_path = config["airport"]["database_path"]
    
    logger.info("=" * 70)
    logger.info("🛫 AIRPORT INR PIPELINE")
    logger.info("=" * 70)
    logger.info(f"Airport: {airport}")
    logger.info(f"Database: {db_path}")
    logger.info("")
    
    # Check database exists
    if not Path(db_path).exists():
        logger.error(f"❌ Database file not found: {db_path}")
        sys.exit(1)
    
    logger.info("📋 Running pipeline stages...\n")
    
    timings = {}
    
    # Stage 1: Extract
    logger.info("▶️  STAGE 1: FEATURE EXTRACTION")
    logger.info("-" * 70)
    try:
        start = time.time()
        from pipelines import extract_buildings
        timings["extract"] = time.time() - start
        logger.info(f"✅ Feature extraction complete ({timings['extract']:.1f}s)\n")
    except Exception as e:
        logger.error(f"❌ Feature extraction failed: {e}")
        sys.exit(1)
    
    # Stage 2: Build Mesh
    logger.info("▶️  STAGE 2: MESH GENERATION")
    logger.info("-" * 70)
    try:
        start = time.time()
        from pipelines import build_mesh
        timings["mesh"] = time.time() - start
        logger.info(f"✅ Mesh generation complete ({timings['mesh']:.1f}s)\n")
    except Exception as e:
        logger.error(f"❌ Mesh generation failed: {e}")
        sys.exit(1)
    
    # Stage 3: Generate SDF
    logger.info("▶️  STAGE 3: SDF DATASET GENERATION")
    logger.info("-" * 70)
    try:
        start = time.time()
        from pipelines import generate_sdf_dataset
        timings["sdf"] = time.time() - start
        logger.info(f"✅ SDF dataset generation complete ({timings['sdf']:.1f}s)\n")
    except Exception as e:
        logger.error(f"❌ SDF dataset generation failed: {e}")
        sys.exit(1)
    
    # Summary
    paths = get_output_paths(airport)
    logger.info("=" * 70)
    logger.info("✅ PIPELINE COMPLETE")
    logger.info("=" * 70)
    logger.info(f"\n⏱️  Timings:")
    logger.info(f"   • Feature extraction: {timings['extract']:.1f}s")
    logger.info(f"   • Mesh generation: {timings['mesh']:.1f}s")
    logger.info(f"   • SDF generation: {timings['sdf']:.1f}s")
    logger.info(f"   • Total: {sum(timings.values()):.1f}s\n")
    
    logger.info(f"📦 Output files:")
    logger.info(f"   • Mesh: {paths['processed_mesh']}")
    logger.info(f"   • Train set: {paths['sdf_train']}")
    logger.info(f"   • Validation set: {paths['sdf_val']}")
    logger.info(f"   • Point cloud: {paths['sdf_points_ply']}")
    logger.info("")


def print_summary(timings: dict) -> None:
    """Affiche le résumé final de la pipeline."""
    pass  # Already printed in run_stages()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run complete airport INR pipeline"
    )
    parser.add_argument(
        "--airport", "-a",
        type=str,
        help="Airport code (e.g., LFPO, LFPG). If not specified, uses config value."
    )
    
    args = parser.parse_args()
    run_stages(airport_code=args.airport)
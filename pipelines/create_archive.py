#!/usr/bin/env python3
"""
Create a zip file with all pipeline outputs for sharing.

Usage:
    python -m pipelines.create_archive LFPO
    python -m pipelines.create_archive LFPO --output my_archive.zip
"""

import sys
import argparse
import logging
from pathlib import Path
import zipfile
from datetime import datetime

from src.core.logging import setup_logger

logger = setup_logger()


def create_archive(airport_code: str, output_file: str | None = None) -> None:
    """Create a zip archive with all pipeline outputs."""
    
    # Build output directory path
    output_dir = Path(f"data/processed/{airport_code}")
    
    if not output_dir.exists():
        logger.error(f"❌ Output directory not found: {output_dir}")
        logger.info(f"   Please run the pipeline for {airport_code} first")
        sys.exit(1)
    
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{airport_code}_inr_dataset_{timestamp}.zip"
    
    output_path = Path(output_file)
    
    logger.info("=" * 70)
    logger.info("📦 CREATING ARCHIVE")
    logger.info("=" * 70)
    logger.info(f"Airport: {airport_code}")
    logger.info(f"Source: {output_dir}")
    logger.info(f"Output: {output_path}")
    logger.info("")
    
    # Files to include
    files_to_zip = [
        output_dir / f"{airport_code}_mesh.obj",
        output_dir / f"{airport_code}_sdf_train.parquet",
        output_dir / f"{airport_code}_sdf_val.parquet",
        output_dir / f"{airport_code}_sdf_points.ply",
        output_dir / f"{airport_code}_normalization_metadata.json",
    ]
    
    # Check all files exist
    missing = [f for f in files_to_zip if not f.exists()]
    if missing:
        logger.error("❌ Missing files:")
        for f in missing:
            logger.error(f"   - {f}")
        sys.exit(1)
    
    # Create zip
    logger.info("📝 Adding files to archive...")
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in files_to_zip:
            arcname = f"{airport_code}/{file_path.name}"
            zf.write(file_path, arcname=arcname)
            size_mb = file_path.stat().st_size / (1024 * 1024)
            logger.info(f"   ✓ {arcname} ({size_mb:.1f} MB)")
    
    # Summary
    zip_size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info("")
    logger.info("=" * 70)
    logger.info("✅ ARCHIVE CREATED")
    logger.info("=" * 70)
    logger.info(f"Archive: {output_path}")
    logger.info(f"Size: {zip_size_mb:.1f} MB")
    logger.info(f"Files: {len(files_to_zip)}")
    logger.info("")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create zip archive of pipeline outputs"
    )
    parser.add_argument(
        "airport",
        type=str,
        help="Airport code (e.g., LFPO, LFPG)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output zip file name. Default: {airport}_inr_dataset_YYYYMMDD_HHMMSS.zip"
    )
    
    args = parser.parse_args()
    create_archive(args.airport, output_file=args.output)

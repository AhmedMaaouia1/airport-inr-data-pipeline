import sqlite3
import pandas as pd
import geopandas as gpd
import logging

logger = logging.getLogger(__name__)


def load_buildings(db_path):

    conn = sqlite3.connect(db_path)
    conn.enable_load_extension(True)
    conn.load_extension("mod_spatialite")

    query = """
    SELECT
        oid,
        building_id,
        height,
        instudy,
        AsBinary(geometry) AS geometry
    FROM shapes_buildings
    """

    df = pd.read_sql(query, conn)

    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.GeoSeries.from_wkb(df["geometry"])
    )

    return gdf


def load_airport_features(db_path):
    """
    Load ALL airport features from OpenALAQS database.
    
    Returns a unified GeoDataFrame with 'feature_type' column.
    
    Feature types:
    - building (from shapes_buildings)
    - runway (from shapes_runways)
    - taxiway (from shapes_taxiways)
    - roadway (from shapes_roadways)
    - parking (from shapes_parking)
    - gate (from shapes_gates)
    - track (from shapes_tracks)
    - point_source (from shapes_point_sources)
    """
    
    conn = sqlite3.connect(db_path)
    conn.enable_load_extension(True)
    conn.load_extension("mod_spatialite")
    
    features = []
    
    # Load buildings
    try:
        query = """
        SELECT
            oid,
            building_id AS feature_id,
            height,
            AsBinary(geometry) AS geometry
        FROM shapes_buildings
        WHERE geometry IS NOT NULL
        """
        df = pd.read_sql(query, conn)
        if len(df) > 0:
            gdf = gpd.GeoDataFrame(
                df,
                geometry=gpd.GeoSeries.from_wkb(df["geometry"]),
                crs="EPSG:4326"
            )
            gdf["feature_type"] = "building"
            features.append(gdf)
            logger.info(f"✓ Buildings loaded: {len(gdf)}")
        else:
            logger.info("✓ Buildings: 0 records")
    except Exception as e:
        logger.warning(f"⚠ Failed to load buildings: {e}")
    
    # Load runways
    try:
        query = """
        SELECT
            oid,
            runway_id AS feature_id,
            AsBinary(geometry) AS geometry
        FROM shapes_runways
        WHERE geometry IS NOT NULL
        """
        df = pd.read_sql(query, conn)
        if len(df) > 0:
            gdf = gpd.GeoDataFrame(
                df,
                geometry=gpd.GeoSeries.from_wkb(df["geometry"]),
                crs="EPSG:4326"
            )
            gdf["feature_type"] = "runway"
            features.append(gdf)
            logger.info(f"✓ Runways loaded: {len(gdf)}")
        else:
            logger.info("✓ Runways: 0 records")
    except Exception as e:
        logger.warning(f"⚠ Failed to load runways: {e}")
    
    # Load taxiways
    try:
        query = """
        SELECT
            oid,
            taxiway_id AS feature_id,
            AsBinary(geometry) AS geometry
        FROM shapes_taxiways
        WHERE geometry IS NOT NULL
        """
        df = pd.read_sql(query, conn)
        if len(df) > 0:
            gdf = gpd.GeoDataFrame(
                df,
                geometry=gpd.GeoSeries.from_wkb(df["geometry"]),
                crs="EPSG:4326"
            )
            gdf["feature_type"] = "taxiway"
            features.append(gdf)
            logger.info(f"✓ Taxiways loaded: {len(gdf)}")
        else:
            logger.info("✓ Taxiways: 0 records")
    except Exception as e:
        logger.warning(f"⚠ Failed to load taxiways: {e}")
    
    # Load roadways
    try:
        query = """
        SELECT
            oid,
            roadway_id AS feature_id,
            AsBinary(geometry) AS geometry
        FROM shapes_roadways
        WHERE geometry IS NOT NULL
        """
        df = pd.read_sql(query, conn)
        if len(df) > 0:
            gdf = gpd.GeoDataFrame(
                df,
                geometry=gpd.GeoSeries.from_wkb(df["geometry"]),
                crs="EPSG:4326"
            )
            gdf["feature_type"] = "roadway"
            features.append(gdf)
            logger.info(f"✓ Roadways loaded: {len(gdf)}")
        else:
            logger.info("✓ Roadways: 0 records")
    except Exception as e:
        logger.warning(f"⚠ Failed to load roadways: {e}")
    
    # Load parking areas
    try:
        query = """
        SELECT
            oid,
            parking_id AS feature_id,
            AsBinary(geometry) AS geometry
        FROM shapes_parking
        WHERE geometry IS NOT NULL
        """
        df = pd.read_sql(query, conn)
        if len(df) > 0:
            gdf = gpd.GeoDataFrame(
                df,
                geometry=gpd.GeoSeries.from_wkb(df["geometry"]),
                crs="EPSG:4326"
            )
            gdf["feature_type"] = "parking"
            features.append(gdf)
            logger.info(f"✓ Parking areas loaded: {len(gdf)}")
        else:
            logger.info("✓ Parking areas: 0 records")
    except Exception as e:
        logger.warning(f"⚠ Failed to load parking: {e}")
    
    # Load gates (points)
    try:
        query = """
        SELECT
            oid,
            gate_id AS feature_id,
            AsBinary(geometry) AS geometry
        FROM shapes_gates
        WHERE geometry IS NOT NULL
        """
        df = pd.read_sql(query, conn)
        if len(df) > 0:
            gdf = gpd.GeoDataFrame(
                df,
                geometry=gpd.GeoSeries.from_wkb(df["geometry"]),
                crs="EPSG:4326"
            )
            gdf["feature_type"] = "gate"
            features.append(gdf)
            logger.info(f"✓ Gates loaded: {len(gdf)}")
        else:
            logger.info("✓ Gates: 0 records")
    except Exception as e:
        logger.warning(f"⚠ Failed to load gates: {e}")
    
    # Load tracks (lines)
    try:
        query = """
        SELECT
            oid,
            track_id AS feature_id,
            AsBinary(geometry) AS geometry
        FROM shapes_tracks
        WHERE geometry IS NOT NULL
        """
        df = pd.read_sql(query, conn)
        if len(df) > 0:
            gdf = gpd.GeoDataFrame(
                df,
                geometry=gpd.GeoSeries.from_wkb(df["geometry"]),
                crs="EPSG:4326"
            )
            gdf["feature_type"] = "track"
            features.append(gdf)
            logger.info(f"✓ Tracks loaded: {len(gdf)}")
        else:
            logger.info("✓ Tracks: 0 records")
    except Exception as e:
        logger.warning(f"⚠ Failed to load tracks: {e}")
    
    # Load point sources (points)
    try:
        query = """
        SELECT
            oid,
            source_id AS feature_id,
            AsBinary(geometry) AS geometry
        FROM shapes_point_sources
        WHERE geometry IS NOT NULL
        """
        df = pd.read_sql(query, conn)
        if len(df) > 0:
            gdf = gpd.GeoDataFrame(
                df,
                geometry=gpd.GeoSeries.from_wkb(df["geometry"]),
                crs="EPSG:4326"
            )
            gdf["feature_type"] = "point_source"
            features.append(gdf)
            logger.info(f"✓ Point sources loaded: {len(gdf)}")
        else:
            logger.info("✓ Point sources: 0 records")
    except Exception as e:
        logger.warning(f"⚠ Failed to load point sources: {e}")
    
    conn.close()
    
    # Merge all features
    if not features:
        raise ValueError("No features loaded from database!")
    
    gdf_merged = gpd.GeoDataFrame(
        pd.concat(features, ignore_index=True),
        crs="EPSG:4326"
    )
    logger.info(f"✓ Total features loaded: {len(gdf_merged)}")
    logger.info(f"  Feature types: {gdf_merged['feature_type'].value_counts().to_dict()}")
    
    return gdf_merged
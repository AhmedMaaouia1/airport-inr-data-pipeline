import sqlite3
import pandas as pd
import geopandas as gpd

db_path = "data/raw/openalaqs/LFPO.sqlite"
conn = sqlite3.connect(db_path)
conn.enable_load_extension(True)
conn.load_extension("mod_spatialite")

# Test loading each feature type
for table, id_col in [
    ("shapes_buildings", "building_id"),
    ("shapes_runways", "runway_id"),
    ("shapes_taxiways", "taxiway_id"),
    ("shapes_roadways", "roadway_id"),
]:
    query = f"""
    SELECT
        oid,
        {id_col} AS feature_id,
        AsBinary(geometry) AS geometry
    FROM {table}
    LIMIT 2
    """
    try:
        df = pd.read_sql(query, conn)
        print(f"\n📍 {table}:")
        print(f"  Rows fetched: {len(df)}")
        print(f"  geometry column type: {df['geometry'].dtype}")
        print(f"  Sample geometry bytes: {df['geometry'].iloc[0][:20] if len(df) > 0 else 'N/A'}")
        
        # Try parsing
        gdf = gpd.GeoDataFrame(
            df,
            geometry=gpd.GeoSeries.from_wkb(df["geometry"]),
            crs="EPSG:4326"
        )
        print(f"  ✓ Parsed successfully: {len(gdf)} geometries")
        print(f"  Geometry types: {gdf.geometry.geom_type.unique()}")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")

conn.close()

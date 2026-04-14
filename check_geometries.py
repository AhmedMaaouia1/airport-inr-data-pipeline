import sqlite3
import pandas as pd

db_path = "data/raw/openalaqs/LFPO.sqlite"
conn = sqlite3.connect(db_path)
conn.enable_load_extension(True)
conn.load_extension("mod_spatialite")

# Check each feature table
for table in ["shapes_buildings", "shapes_runways", "shapes_taxiways", "shapes_roadways"]:
    query = f"""
    SELECT 
        COUNT(*) as total_records,
        SUM(CASE WHEN geometry IS NULL THEN 1 ELSE 0 END) as null_geometries,
        SUM(CASE WHEN ST_IsEmpty(geometry) THEN 1 ELSE 0 END) as empty_geometries,
        SUM(CASE WHEN geometry IS NOT NULL AND NOT ST_IsEmpty(geometry) THEN 1 ELSE 0 END) as valid_geometries
    FROM {table}
    """
    try:
        df = pd.read_sql(query, conn)
        print(f"\n📊 {table}:")
        for col, val in df.iloc[0].items():
            print(f"   {col}: {val}")
    except Exception as e:
        print(f"\n❌ {table}: {e}")

conn.close()

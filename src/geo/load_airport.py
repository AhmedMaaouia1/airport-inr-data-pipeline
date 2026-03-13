import sqlite3
import pandas as pd
import geopandas as gpd


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
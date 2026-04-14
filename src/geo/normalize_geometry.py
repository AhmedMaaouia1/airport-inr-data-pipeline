import logging
from shapely.geometry import Polygon, MultiPolygon, LineString, Point
import geopandas as gpd

logger = logging.getLogger(__name__)


def normalize_geometries(gdf):
    """
    Convert all geometries to Polygons.
    
    Rules:
    - POLYGON → keep as is
    - MULTIPOLYGON → explode into individual polygons
    - LINESTRING → buffer to 1m width
    - POINT → buffer to 1m radius circle
    - MULTIPOINT → buffer each point, then union
    - MULTILINESTRING → buffer to 1m width, then union
    
    Returns GeoDataFrame with only Polygon geometries.
    """
    
    normalized_rows = []
    
    for idx, row in gdf.iterrows():
        geom = row.geometry
        
        if geom is None or geom.is_empty:
            continue
        
        # POLYGON: keep as is
        if geom.geom_type == "Polygon":
            normalized_rows.append(row)
        
        # MULTIPOLYGON: explode into individual polygons
        elif geom.geom_type == "MultiPolygon":
            for poly in geom.geoms:
                row_copy = row.copy()
                row_copy.geometry = poly
                normalized_rows.append(row_copy)
        
        # LINESTRING: buffer to polygon
        elif geom.geom_type == "LineString":
            buffered = geom.buffer(1.0)  # 1m buffer on each side
            if not buffered.is_empty:
                row_copy = row.copy()
                row_copy.geometry = buffered
                normalized_rows.append(row_copy)
        
        # MULTILINESTRING: buffer each line and union
        elif geom.geom_type == "MultiLineString":
            buffered_geoms = [line.buffer(1.0) for line in geom.geoms]
            union_geom = gpd.GeoSeries(buffered_geoms).unary_union
            if not union_geom.is_empty and union_geom.geom_type == "Polygon":
                row_copy = row.copy()
                row_copy.geometry = union_geom
                normalized_rows.append(row_copy)
        
        # POINT: buffer to circle
        elif geom.geom_type == "Point":
            buffered = geom.buffer(1.0)  # 1m radius circle
            if not buffered.is_empty:
                row_copy = row.copy()
                row_copy.geometry = buffered
                normalized_rows.append(row_copy)
        
        # MULTIPOINT: buffer each point and union
        elif geom.geom_type == "MultiPoint":
            buffered_geoms = [pt.buffer(1.0) for pt in geom.geoms]
            union_geom = gpd.GeoSeries(buffered_geoms).unary_union
            if not union_geom.is_empty and union_geom.geom_type == "Polygon":
                row_copy = row.copy()
                row_copy.geometry = union_geom
                normalized_rows.append(row_copy)
        
        else:
            logger.warning(f"Unknown geometry type: {geom.geom_type}, skipping")
    
    if not normalized_rows:
        raise ValueError("No valid geometries after normalization!")
    
    gdf_normalized = gpd.GeoDataFrame(normalized_rows, crs=gdf.crs)
    logger.info(f"✓ Geometric normalization complete: {len(gdf_normalized)} polygons")
    
    return gdf_normalized


def clean_and_normalize_geometries(gdf):
    """
    Clean geometries (fix self-intersections) and normalize to polygons.
    
    For polygons: apply buffer(0) first
    For lines/points: normalize first, then apply buffer(0)
    """
    
    normalized_and_cleaned = []
    
    for idx, row in gdf.iterrows():
        geom = row.geometry
        
        if geom is None or geom.is_empty:
            continue
        
        try:
            # For polygons: buffer(0) first to fix self-intersections
            if geom.geom_type == "Polygon":
                fixed_geom = geom.buffer(0)
                if not fixed_geom.is_empty:
                    row_copy = row.copy()
                    row_copy.geometry = fixed_geom
                    normalized_and_cleaned.append(row_copy)
            
            # For lines: buffer first (normalize), then buffer(0)
            elif geom.geom_type == "LineString":
                buffered = geom.buffer(1.0)  # 1m buffer
                if not buffered.is_empty:
                    fixed_geom = buffered.buffer(0)
                    if not fixed_geom.is_empty:
                        row_copy = row.copy()
                        row_copy.geometry = fixed_geom
                        normalized_and_cleaned.append(row_copy)
            
            elif geom.geom_type == "MultiLineString":
                buffered_geoms = [line.buffer(1.0) for line in geom.geoms]
                union_geom = gpd.GeoSeries(buffered_geoms).unary_union
                if not union_geom.is_empty:
                    fixed_geom = union_geom.buffer(0)
                    if not fixed_geom.is_empty:
                        row_copy = row.copy()
                        row_copy.geometry = fixed_geom
                        normalized_and_cleaned.append(row_copy)
            
            # For points: buffer to create polygon, then buffer(0)
            elif geom.geom_type == "Point":
                buffered = geom.buffer(1.0)  # 1m buffer
                if not buffered.is_empty:
                    fixed_geom = buffered.buffer(0)
                    if not fixed_geom.is_empty:
                        row_copy = row.copy()
                        row_copy.geometry = fixed_geom
                        normalized_and_cleaned.append(row_copy)
            
            elif geom.geom_type == "MultiPoint":
                buffered_geoms = [pt.buffer(1.0) for pt in geom.geoms]
                union_geom = gpd.GeoSeries(buffered_geoms).unary_union
                if not union_geom.is_empty:
                    fixed_geom = union_geom.buffer(0)
                    if not fixed_geom.is_empty:
                        row_copy = row.copy()
                        row_copy.geometry = fixed_geom
                        normalized_and_cleaned.append(row_copy)
            
            elif geom.geom_type == "MultiPolygon":
                for poly in geom.geoms:
                    fixed_geom = poly.buffer(0)
                    if not fixed_geom.is_empty:
                        row_copy = row.copy()
                        row_copy.geometry = fixed_geom
                        normalized_and_cleaned.append(row_copy)
            
            else:
                logger.warning(f"Unknown geometry type: {geom.geom_type}, skipping")
        
        except Exception as e:
            logger.warning(f"Failed to process geometry: {e}")
    
    if not normalized_and_cleaned:
        raise ValueError("No valid geometries after cleaning and normalization!")
    
    gdf_result = gpd.GeoDataFrame(normalized_and_cleaned, crs=gdf.crs)
    logger.info(f"✓ Geometry cleanup & normalization: {len(gdf_result)} valid polygons")
    
    return gdf_result

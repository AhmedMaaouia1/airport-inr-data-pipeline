import trimesh
import logging

logger = logging.getLogger(__name__)


def extrude_buildings(gdf, default_height=15):

    meshes = []

    for _, row in gdf.iterrows():

        polygon = row.geometry

        height = row.height

        if height is None:
            height = default_height

        mesh = trimesh.creation.extrude_polygon(
            polygon,
            height
        )

        meshes.append(mesh)

    return meshes


def extrude_features(gdf, heights_config):
    """
    Generalized feature extrusion for ALL feature types.
    
    Parameters:
    -----------
    gdf : GeoDataFrame
        Must have columns: geometry, feature_type, and optionally 'height'
    
    heights_config : dict
        Extrusion heights per feature type, e.g.:
        {
            'building': 15.0,
            'runway': 0.1,
            'taxiway': 0.1,
            'roadway': 0.05,
            'parking': 0.05,
            'gate': 0.02,
            'track': 0.02,
            'point_source': 0.02
        }
    
    Returns:
    --------
    list of trimesh.Mesh objects
    """
    
    meshes = []
    feature_stats = {}
    
    for idx, row in gdf.iterrows():
        
        polygon = row.geometry
        feature_type = row["feature_type"]
        
        # Get extrusion height
        if feature_type == "building" and "height" in row and row["height"] is not None:
            # Buildings can have individual heights
            height = row["height"]
        else:
            # Use default from config
            height = heights_config.get(feature_type, 0.1)
        
        try:
            mesh = trimesh.creation.extrude_polygon(polygon, height)
            meshes.append(mesh)
            
            # Track statistics
            if feature_type not in feature_stats:
                feature_stats[feature_type] = 0
            feature_stats[feature_type] += 1
            
        except Exception as e:
            logger.warning(f"Failed to extrude {feature_type} (id={idx}): {e}")
    
    logger.info(f"✓ Feature extrusion complete: {len(meshes)} meshes generated")
    for ftype, count in sorted(feature_stats.items()):
        logger.info(f"  - {ftype}: {count} meshes")
    
    return meshes

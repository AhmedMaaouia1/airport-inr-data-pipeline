import geopandas as gpd
from src.core.logging import setup_logger

logger = setup_logger()


def clean_buildings(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Nettoie les géométries d'un GeoDataFrame de bâtiments.

    Étapes :
    - Suppression des géométries nulles
    - Correction des polygones auto-intersectés (buffer(0))
    - Suppression des géométries vides après correction

    Returns:
        GeoDataFrame nettoyé
    """
    initial_count = len(gdf)

    # 1. Supprimer les géométries nulles
    gdf = gdf[gdf.geometry.notnull()].copy()
    after_null = len(gdf)
    removed_null = initial_count - after_null
    if removed_null:
        logger.warning("Géométries nulles supprimées : %d", removed_null)

    # 2. Corriger les géométries invalides via buffer(0)
    invalid_mask = ~gdf.is_valid
    if invalid_mask.any():
        logger.warning("Géométries invalides détectées : %d — correction via buffer(0)", invalid_mask.sum())
        gdf.loc[invalid_mask, "geometry"] = gdf.loc[invalid_mask, "geometry"].buffer(0)

    # 3. Supprimer les géométries vides restantes
    gdf = gdf[~gdf.geometry.is_empty].copy()
    after_empty = len(gdf)
    removed_empty = after_null - after_empty
    if removed_empty:
        logger.warning("Géométries vides supprimées après correction : %d", removed_empty)

    # 4. Filtrer toute géométrie encore invalide
    gdf = gdf[gdf.is_valid].copy()
    final_count = len(gdf)
    total_removed = initial_count - final_count

    logger.info(
        "Nettoyage terminé : %d bâtiments conservés sur %d (%d supprimés)",
        final_count, initial_count, total_removed
    )

    return gdf.reset_index(drop=True)

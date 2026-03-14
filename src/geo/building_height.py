import geopandas as gpd
import pandas as pd
from src.core.logging import setup_logger

logger = setup_logger()

DEFAULT_HEIGHT = 15.0       # mètres — hauteur par défaut si aucune donnée
METERS_PER_LEVEL = 3.5      # mètres par étage


def estimate_building_height(gdf: gpd.GeoDataFrame, default_height: float = DEFAULT_HEIGHT) -> gpd.GeoDataFrame:
    """
    Estime la hauteur des bâtiments selon la logique suivante :
      1. Utilise la colonne 'height' si la valeur est présente et positive
      2. Sinon, utilise 'building:levels' * METERS_PER_LEVEL si disponible
      3. Sinon, applique la hauteur par défaut (default_height)

    Args:
        gdf:            GeoDataFrame des bâtiments
        default_height: Hauteur par défaut en mètres (défaut : 15 m)

    Returns:
        GeoDataFrame avec une colonne 'height' complète (float)
    """
    gdf = gdf.copy()

    # S'assurer que 'height' est numérique
    gdf["height"] = pd.to_numeric(gdf.get("height"), errors="coerce")

    # Initialiser la colonne finale
    gdf["height_estimated"] = gdf["height"]

    # Utiliser building:levels si height manquante
    if "building:levels" in gdf.columns:
        levels = pd.to_numeric(gdf["building:levels"], errors="coerce")
        mask_no_height = gdf["height_estimated"].isna() | (gdf["height_estimated"] <= 0)
        mask_has_levels = mask_no_height & levels.notna() & (levels > 0)
        gdf.loc[mask_has_levels, "height_estimated"] = levels[mask_has_levels] * METERS_PER_LEVEL

        n_from_levels = mask_has_levels.sum()
        if n_from_levels:
            logger.info("Hauteur estimée via building:levels pour %d bâtiments", n_from_levels)

    # Appliquer la hauteur par défaut pour le reste
    mask_still_missing = gdf["height_estimated"].isna() | (gdf["height_estimated"] <= 0)
    n_default = mask_still_missing.sum()
    if n_default:
        logger.info("Hauteur par défaut (%.1f m) appliquée pour %d bâtiments", default_height, n_default)
    gdf.loc[mask_still_missing, "height_estimated"] = default_height

    # Remplacer height par la valeur estimée
    gdf["height"] = gdf["height_estimated"].astype(float)
    gdf = gdf.drop(columns=["height_estimated"])

    logger.info(
        "Hauteurs finales — min: %.1f m | max: %.1f m | moyenne: %.1f m",
        gdf["height"].min(),
        gdf["height"].max(),
        gdf["height"].mean(),
    )

    return gdf

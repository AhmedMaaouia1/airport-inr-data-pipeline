import pandas as pd
from src.core.logging import setup_logger

logger = setup_logger()


def validate_sdf_dataset(df: pd.DataFrame) -> None:
    """
    Valide la qualité d'un dataset SDF (x, y, z, s).

    Vérifications :
    - Colonnes attendues présentes
    - Absence de valeurs NaN
    - Distribution des distances (statistiques descriptives)
    - Présence de valeurs positives et négatives (intérieur/extérieur)

    Raises:
        ValueError: si le dataset ne passe pas une vérification critique.
    """
    logger.info("=== Validation du dataset SDF ===")

    # 1. Colonnes attendues
    expected_cols = {"x", "y", "z", "s"}
    missing_cols = expected_cols - set(df.columns)
    if missing_cols:
        raise ValueError(f"Colonnes manquantes dans le dataset : {missing_cols}")
    logger.info("[OK] Colonnes : %s", list(df.columns))

    # 2. Taille du dataset
    logger.info("[OK] Nombre de points : %d", len(df))

    # 3. Valeurs NaN
    nan_counts = df[list(expected_cols)].isna().sum()
    total_nans = nan_counts.sum()
    if total_nans > 0:
        raise ValueError(f"NaN détectés dans le dataset :\n{nan_counts[nan_counts > 0]}")
    logger.info("[OK] Aucun NaN détecté")

    # 4. Statistiques sur la SDF
    sdf = df["s"]
    stats = {
        "min":  sdf.min(),
        "max":  sdf.max(),
        "mean": sdf.mean(),
        "std":  sdf.std(),
    }
    logger.info(
        "[OK] Distribution SDF — min: %.4f | max: %.4f | mean: %.4f | std: %.4f",
        stats["min"], stats["max"], stats["mean"], stats["std"]
    )

    # 5. Vérification que le dataset contient des points intérieurs et extérieurs
    n_positive = (sdf > 0).sum()
    n_negative = (sdf < 0).sum()
    n_zero     = (sdf == 0).sum()
    logger.info(
        "[OK] Répartition SDF — positifs (libre): %d | négatifs (intérieur): %d | nuls (surface): %d",
        n_positive, n_negative, n_zero
    )

    if n_positive == 0:
        logger.warning("[WARN] Aucun point avec SDF > 0 — vérifier le sampling free space")
    if n_negative == 0:
        logger.warning("[WARN] Aucun point avec SDF < 0 — vérifier la fermeture du mesh (watertight)")

    # 6. Coordonnées normalisées dans [-1, 1]
    for col in ["x", "y", "z"]:
        col_min = df[col].min()
        col_max = df[col].max()
        if col_min < -1.1 or col_max > 1.1:
            logger.warning(
                "[WARN] Colonne '%s' hors de [-1, 1] : min=%.4f, max=%.4f — vérifier la normalisation",
                col, col_min, col_max
            )

    logger.info("=== Validation terminée avec succès ===")

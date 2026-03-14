# Documentation technique — Airport INR Data Pipeline

## Vue d'ensemble

Ce pipeline transforme des données brutes géospatiales d'aéroport (base OpenALAQS) en un dataset d'entraînement pour un réseau neuronal à représentation implicite (INR). Le dataset produit associe des coordonnées 3D `(x, y, z)` à leur valeur de **Signed Distance Function (SDF)**, c'est-à-dire la distance signée au mesh de l'aéroport.

---

## Architecture du pipeline

```
data/raw/openalaqs/LFPO_Project.sqlite
            │
            ▼
    ┌────────────────────┐
    │  extract_buildings  │   Extraction + nettoyage + estimation hauteurs
    └─────────┬──────────┘
              │  data/staging/buildings.parquet
              ▼
    ┌────────────────────┐
    │    build_mesh       │   Extrusion 3D + fusion → mesh global
    └─────────┬──────────┘
              │  data/processed/{airport_code}/{airport_code}_mesh.obj
              ▼
    ┌──────────────────────────┐
    │  generate_sdf_dataset    │   Sampling + calcul SDF + normalisation
    └─────────┬────────────────┘
              │
              ├── data/processed/{airport_code}/{airport_code}_sdf_train.parquet
              ├── data/processed/{airport_code}/{airport_code}_sdf_val.parquet
              └── data/processed/{airport_code}/{airport_code}_sdf_points.ply
```

---

## Rôle de chaque dossier

| Dossier | Rôle |
|---|---|
| `config/` | Configuration centralisée du pipeline (YAML) |
| `data/raw/` | Données brutes non versionnées (SQLite OpenALAQS) |
| `data/staging/` | Données intermédiaires nettoyées (GeoParquet bâtiments) |
| `data/processed/` | Sorties finales : mesh OBJ, datasets Parquet, nuage PLY |
| `pipelines/` | Scripts exécutables de chaque étape + orchestrateur |
| `src/core/` | Utilitaires transverses : config, logging, normalisation |
| `src/geo/` | Chargement, nettoyage et enrichissement géospatial |
| `src/mesh/` | Construction du mesh 3D (extrusion, fusion) |
| `src/sdf/` | Sampling 3D et calcul de la SDF |
| `src/validation/` | Contrôle qualité du dataset |
| `src/visualization/` | Outils de visualisation interactive |
| `Docker/` | Image Docker reproductible |
| `docs/` | Documentation technique |

---

## Étapes détaillées

### Étape 1 — `extract_buildings.py`

**Objectif** : extraire les bâtiments de la base SQLite et produire un fichier GeoParquet propre.

**Modules impliqués** :
- `src/geo/load_airport.py` — connexion à la base via `sqlite3` + extension **SpatiaLite**, requête SQL sur `shapes_buildings`, conversion WKB → GeoDataFrame
- `src/geo/clean_geometries.py` — nettoyage des géométries (nulles, invalides, vides)
- `src/geo/building_height.py` — estimation des hauteurs manquantes

**Logique d'estimation des hauteurs** :
```
SI height présent et > 0     → utiliser height
SINON SI building:levels > 0 → hauteur = levels × 3.5 m
SINON                         → hauteur par défaut (config)
```

**Sortie** : `data/staging/buildings.parquet`

---

### Étape 2 — `build_mesh.py`

**Objectif** : construire le mesh 3D de l'aéroport à partir des emprises 2D.

**Modules impliqués** :
- `src/mesh/extrude_buildings.py` — extrusion verticale de chaque polygone 2D →  prisme 3D via `trimesh.creation.extrude_polygon`
- `src/mesh/merge_meshes.py` — concaténation de tous les meshes individuels en un mesh global

**Vérifications mesh** :
- `is_watertight` — si `True`, le calcul SDF est plus fiable (intérieur/extérieur bien définis)
- Nombre de composantes connexes

**Sortie** : `data/processed/{airport_code}/{airport_code}_mesh.obj`

---

### Étape 3 — `generate_sdf_dataset.py`

**Objectif** : générer le dataset `(x, y, z, SDF)` pour l'entraînement de l'INR.

#### Stratégies de sampling

| Source | Module | Points (défaut) | Description |
|---|---|---|---|
| Surface | `sample_surface.py` | 20 000 | Points tirés uniformément sur la surface du mesh |
| Near-surface | `sample_near_surface.py` | 20 000 | Points de surface + bruit gaussien (σ = 0.02) |
| Free space | `sample_free_space.py` | 20 000 | Points aléatoires dans la bounding box (z ∈ [0, 80 m]) |

Le sampling mixte est crucial pour un apprentissage INR de qualité :
- **Surface** : SDF ≈ 0, apprentissage de la géométrie précise
- **Near-surface** : gradient fort, apprentissage de la normale locale
- **Free space** : SDF ≫ 0, apprentissage des zones libres

#### Calcul SDF

La SDF est calculée via `trimesh.proximity.signed_distance` en **chunks** de 5 000 points pour éviter les dépassements mémoire sur les grands datasets.

#### Normalisation

Toutes les coordonnées et distances sont normalisées dans `[-1, 1]` :
- `center = (min + max) / 2`
- `scale = max_range / 2`
- `points_normalized = (points - center) / scale`
- `distances_normalized = distances / scale`

#### Validation

Après construction, `validate_sdf_dataset()` vérifie :
- Absence de NaN
- Présence de valeurs SDF positives et négatives
- Coordonnées normalisées dans `[-1, 1]`
- Statistiques descriptives (min, max, mean, std)

**Sorties** :
- `data/processed/{airport_code}/{airport_code}_sdf_train.parquet` — 90 % des données
- `data/processed/{airport_code}/{airport_code}_sdf_val.parquet`   — 10 % des données
- `data/processed/{airport_code}/{airport_code}_sdf_points.ply`    — nuage de points pour visualisation

---

## Scalabilite multi-aeroports

Le pipeline est maintenant structurellement **multi-aeroports** :

- le changement d'aeroport se fait uniquement via `config/base.yaml`
- `airport.code` identifie l'aeroport cible
- `airport.database_path` pointe vers la base OpenALAQS correspondante
- les sorties sont ecrites dans un sous-dossier dedie a chaque aeroport

Exemples de sorties :

- `data/processed/LFPO/LFPO_mesh.obj`
- `data/processed/LFPG/LFPG_sdf_train.parquet`
- `data/processed/LFPB/LFPB_sdf_points.ply`

Cette organisation evite d'ecraser les resultats lors de l'execution du pipeline sur plusieurs aeroports.

---

## Structure du dataset SDF

Chaque ligne correspond à un point 3D avec sa valeur SDF :

| Colonne | Type | Description |
|---|---|---|
| `x` | float | Coordonnée X normalisée ∈ [-1, 1] |
| `y` | float | Coordonnée Y normalisée ∈ [-1, 1] |
| `z` | float | Coordonnée Z normalisée ∈ [-1, 1] |
| `s` | float | SDF normalisée : distance signée au mesh |

**Convention SDF** :

| Valeur | Signification |
|---|---|
| `s > 0` | Point dans l'espace libre (extérieur au bâtiment) |
| `s < 0` | Point à l'intérieur d'un bâtiment |
| `s ≈ 0` | Point sur la surface du bâtiment |

---

## Configuration (`config/base.yaml`)

Tous les paramètres du pipeline sont centralisés :

```yaml
airport:
  code: LFPO
  database_path: data/raw/openalaqs/LFPO_Project.sqlite
  default_building_height: 15.0     # Hauteur par défaut en mètres

sampling:
  surface_points: 20000
  near_surface_noise: 0.02          # Sigma du bruit gaussien near-surface
  free_space_points: 20000

sdf:
  chunk_size: 5000                  # Points traités par batch lors du calcul SDF

dataset:
  train_split: 0.9                  # Proportion train / validation

paths:
  staging_buildings: data/staging/buildings.parquet
  processed_root: data/processed
```

Les fichiers finaux sont construits dynamiquement dans le code a partir de `airport.code` :

- `data/processed/{airport_code}/{airport_code}_mesh.obj`
- `data/processed/{airport_code}/{airport_code}_sdf_train.parquet`
- `data/processed/{airport_code}/{airport_code}_sdf_val.parquet`
- `data/processed/{airport_code}/{airport_code}_sdf_points.ply`

---

## Lancement

```bash
# Pipeline complète (recommandé)
python pipelines/run_pipeline.py

# Étapes individuelles
python pipelines/extract_buildings.py
python pipelines/build_mesh.py
python pipelines/generate_sdf_dataset.py

# Visualisation du mesh
python pipelines/view_airport_mesh.py
```

---

## Reproductibilité — Docker

```bash
docker-compose build
docker-compose run pipeline python pipelines/run_pipeline.py
```

L'image Docker installe automatiquement toutes les dépendances système (GDAL, SpatiaLite, libspatialindex) et Python nécessaires.

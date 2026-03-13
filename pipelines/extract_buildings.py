from src.geo.load_airport import load_buildings

DB_PATH = "data/raw/openalaqs/LFPO_Project.sqlite"

gdf = load_buildings(DB_PATH)

print("Nombre de bâtiments :", len(gdf))

print("\nBounding box :")
print(gdf.total_bounds)
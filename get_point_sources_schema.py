import sqlite3

conn = sqlite3.connect("data/raw/openalaqs/LFPO.sqlite")
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(shapes_point_sources)")
columns = cursor.fetchall()

print("Columns in shapes_point_sources:")
for col in columns:
    col_id, col_name, col_type, notnull, default, pk = col
    print(f"  - {col_name}: {col_type}")

conn.close()

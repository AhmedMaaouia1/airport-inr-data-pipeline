import sqlite3
from pathlib import Path

db_path = Path("data/raw/openalaqs/LFPO.sqlite")
print(f"📂 Inspecting database: {db_path}")
print(f"✓ Database exists: {db_path.exists()}\n")

if db_path.exists():
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Try to load SpatiaLite extension
        cursor.enable_load_extension(True)
        cursor.execute("SELECT load_extension('mod_spatialite')")
    except:
        print("⚠️  SpatiaLite extension not available, continuing...\n")
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = cursor.fetchall()
    
    print(f"📊 Found {len(tables)} tables:\n")
    for table in tables:
        table_name = table[0]
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  • {table_name}: {count} rows")
        except Exception as e:
            print(f"  • {table_name}: [error reading count: {str(e)[:30]}...]")
    
    # Show detailed info for shape-related tables
    print("\n" + "="*60)
    print("📋 Detailed info for geometry tables:")
    print("="*60)
    
    for table in tables:
        table_name = table[0]
        if any(keyword in table_name.lower() for keyword in ['shape', 'geometry', 'building', 'runway', 'taxiway', 'parking', 'gate', 'track', 'point']):
            print(f"\n📍 Table: {table_name}")
            try:
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                for col in columns:
                    col_id, col_name, col_type, notnull, default, pk = col
                    print(f"    - {col_name}: {col_type}")
            except Exception as e:
                print(f"    [Error reading schema: {str(e)[:50]}...]")
    
    conn.close()
else:
    print("❌ Database file not found!")

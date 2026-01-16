
import sqlite3
import os

# Database path
DB_PATH = "temis.db"

def fix_schema():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return

    print(f"Connecting to {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Columns to check/add
    columns_to_add = [
        ("description", "TEXT"),
        ("start_date", "DATE"),
        ("end_date", "DATE"),
        ("created_at", "DATETIME"),
        ("updated_at", "DATETIME")
    ]

    for col_name, col_type in columns_to_add:
        try:
            print(f"Adding column '{col_name}'...")
            cursor.execute(f"ALTER TABLE phases ADD COLUMN {col_name} {col_type}")
            print(f"✅ Column '{col_name}' added successfully.")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e):
                print(f"ℹ️ Column '{col_name}' already exists.")
            else:
                print(f"❌ Error adding '{col_name}': {e}")

    conn.commit()
    conn.close()
    print("Schema update completed.")

if __name__ == "__main__":
    fix_schema()

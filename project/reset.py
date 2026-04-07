# reset_database.py - Reset database, keeping only district data

import os
from model_v2 import init_db, Base, get_session, School

print("\n" + "="*60)
print("Reset Database")
print("="*60)

# Delete old database
db_file = 'polling_v2.db'
if os.path.exists(db_file):
    print(f"\nDeleting old database: {db_file}")
    os.remove(db_file)
    print("Deleted successfully")
else:
    print(f"\nDatabase file not found: {db_file}")

# Create new database
print("\nCreating new database...")
engine = init_db(f'sqlite:///{db_file}')

# Create all tables
Base.metadata.create_all(engine)
print("Database tables created")

# Verify tables
db = get_session(engine)

from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()

print("\nCreated tables:")
for table in tables:
    print(f"  - {table}")

# Check district data
school_count = db.query(School).count()
print(f"\nDistrict data: {school_count} records")

if school_count == 0:
    print("\nHint: District data is empty, please run:")
    print("  python import_schools.py")

db.close()

print("\n" + "="*60)
print("Database reset complete!")
print("="*60)

print("\nNext steps:")
print("1. Run: python import_schools.py  (import district data)")
print("2. Run: python create_admin_v2.py  (create admin account)")
print("3. Run: python app_v2.py  (start application)")
print()
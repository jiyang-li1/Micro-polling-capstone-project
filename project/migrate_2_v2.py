# migrate_add_poll_districts.py - Add poll_districts table

from model_v2 import init_db, Base, get_session, poll_districts
from sqlalchemy import inspect

print("\n" + "="*60)
print("Add poll_districts association table")
print("="*60)

# Connect to database
engine = init_db('sqlite:///polling_v2.db')

# Check if table already exists
inspector = inspect(engine)
existing_tables = inspector.get_table_names()

print(f"\nCurrent tables: {existing_tables}")

if 'poll_districts' in existing_tables:
    print("\npoll_districts table already exists, skipping")
else:
    print("\nCreating poll_districts table...")
    # Only create this new table
    Base.metadata.tables['poll_districts'].create(engine)
    print("Created successfully!")

# Verify
inspector = inspect(engine)
if 'poll_districts' in inspector.get_table_names():
    print("\nVerified: poll_districts table created")

    # Show table structure
    columns = inspector.get_columns('poll_districts')
    print("\nTable structure:")
    for col in columns:
        print(f"  - {col['name']}: {col['type']}")
else:
    print("\nError: Table creation failed")

print("\n" + "="*60)
print("Migration complete!")
print("="*60 + "\n")
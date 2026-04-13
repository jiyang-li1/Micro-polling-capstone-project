# import_schools.py - Import district data into the database

import pandas as pd
from model import init_db, get_session, School

print("\n" + "="*60)
print("Import district data to school district database")
print("="*60)

# Initialize database
engine = init_db('sqlite:///polling_v2.db')
db = get_session(engine)

# Clear old data
print("\nClearing old district data...")
db.query(School).delete()
db.commit()

# Read Excel file
excel_file = '../CDESchoolDirectoryExport.xlsx'
print(f"\nReading data from {excel_file}...")

try:
    df = pd.read_excel(excel_file)
    df.dropna(how='all', inplace=True)  # Remove all-empty rows
    print(f"Read {len(df)} rows of data")
    
    count = 0
    errors = 0
    
    for idx, row in df.iterrows():
        try:
            # Extract zip code (remove suffix, e.g. 94544-1136 -> 94544)
            zip_code = str(row['Street Zip']).split('-')[0] if pd.notna(row['Street Zip']) else None
            
            # Handle "No Data"
            school_name = row['School'] if row['School'] != 'No Data' else None
            
            school = School(
                cds_code=str(row['CDS Code']),
                record_type=str(row['Record Type']),
                county=str(row['County']),
                district=str(row['District']),
                school=school_name,
                status=str(row['Status']) if pd.notna(row['Status']) else None,
                entity_type=str(row['Entity Type']) if pd.notna(row['Entity Type']) else None,
                city=str(row['Street City']) if pd.notna(row['Street City']) else None,
                zip_code=zip_code
            )
            
            db.add(school)
            count += 1
            
            # Commit every 1000 records
            if count % 1000 == 0:
                db.commit()
                print(f"Imported {count} records...")

        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"Error (row {idx+2}): {e}")
    
    db.commit()
    
    print(f"\nSuccessfully imported {count} school/district records.")
    if errors > 0:
        print(f"Warning: skipped {errors} error records")

except FileNotFoundError:
    print(f"\nError: file not found: {excel_file}")
    print("Please ensure the file is in the project root directory")
except Exception as e:
    print(f"\nImport failed: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()

# Show statistics
print("\n" + "="*60)
print("Data Statistics:")
print("="*60)

total = db.query(School).count()
districts = db.query(School).filter_by(record_type='District').count()
schools = db.query(School).filter_by(record_type='School').count()
counties = db.query(School.county).distinct().count()
cities = db.query(School.city).distinct().count()
zips = db.query(School.zip_code).distinct().count()

print(f"Total records: {total}")
print(f"  - Districts: {districts}")
print(f"  - Schools: {schools}")
print(f"Counties: {counties}")
print(f"Cities: {cities}")
print(f"Zip Codes: {zips}")

# Show sample districts
print("\nSample districts (first 10):")
sample_districts = db.query(School).filter_by(record_type='District').limit(10).all()
for s in sample_districts:
    print(f"  {s.district:50s} | {s.city:15s} | {s.county}")

print("="*60)

db.close()
print("\nImport complete.\n")
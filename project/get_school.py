# import_schools.py - Import district data

import pandas as pd
from model_v2 import init_db, get_session, Base
from sqlalchemy import Column, Integer, String, Index


class School(Base):

    __tablename__ = 'schools'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cds_code = Column(String(20), unique=True, nullable=False, index=True)
    record_type = Column(String(20), nullable=False)  # District or School
    county = Column(String(100), nullable=False, index=True)
    district = Column(String(200), nullable=False, index=True)
    school = Column(String(200))
    status = Column(String(50))
    entity_type = Column(String(100))
    city = Column(String(100), index=True)
    zip_code = Column(String(10), index=True)
    
    __table_args__ = (
        Index('idx_district_city', 'district', 'city'),
        Index('idx_county_district', 'county', 'district'),
    )
    
    def __repr__(self):
        return f"<School(cds={self.cds_code}, district='{self.district}')>"




engine = init_db('sqlite:///polling_v2.db')


Base.metadata.create_all(engine)

db = get_session(engine)


db.query(School).delete()
db.commit()

# Read Excel file
excel_file = '../CDESchoolDirectoryExport.xlsx'


try:
    df = pd.read_excel(excel_file)
    df.dropna(how='all', inplace=True)  # Remove all-empty rows

    print(f"Columns: {df.columns.tolist()}")
    
    # Map column names
    column_mapping = {
        'CDS Code': 'cds_code',
        'Record Type': 'record_type',
        'County': 'county',
        'District': 'district',
        'School': 'school',
        'Status': 'status',
        'Entity Type': 'entity_type',
        'Street City': 'city',
        'Street Zip': 'zip_code'
    }
    
    count = 0
    errors = 0
    
    for idx, row in df.iterrows():
        try:

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
            if errors <= 5:  # Only show the first 5 errors
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



total = db.query(School).count()
districts = db.query(School).filter_by(record_type='District').count()
schools = db.query(School).filter_by(record_type='School').count()
counties = db.query(School.county).distinct().count()
cities = db.query(School.city).distinct().count()
zips = db.query(School.zip_code).distinct().count()

print(f"Counts: {total}")
print(f" Districts: {districts}")
print(f" Schools: {schools}")


# Show sample data
print("\nSample data (first 10):")
samples = db.query(School).limit(10).all()
for s in samples:
    print(f"  {s.record_type:8s} | {s.district:40s} | {s.city:15s} | {s.zip_code}")

print("="*60)

db.close()
print("\nfinish\n")
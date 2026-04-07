# fix_district_zipcodes.py - Sync zip codes from schools table to zipcodes table

from model_v2 import init_db, get_session, School, ZipCode

engine = init_db('sqlite:///polling_v2.db')
db = get_session(engine)

print("\n" + "="*60)
print("Sync district zip codes to zipcodes table")
print("="*60)

# Get all district zip codes
school_zipcodes = db.query(
    School.zip_code,
    School.city,
    School.county
).filter(
    School.zip_code.isnot(None)
).distinct().all()

print(f"\nFound {len(school_zipcodes)} unique zip codes in schools table")

added = 0
existing = 0

for zip_code, city, county in school_zipcodes:
    # Check if already exists
    zc = db.query(ZipCode).filter_by(zip_code=zip_code).first()
    
    if not zc:
        # Create new zip code
        zc = ZipCode(
            zip_code=zip_code,
            city=city,
            state='CA',
            county=county
        )
        db.add(zc)
        added += 1
        
        if added % 100 == 0:
            db.commit()
            print(f"Added {added} zip codes...")
    else:
        existing += 1

db.commit()

print(f"\nDone!")
print(f"  New zip codes: {added}")
print(f"  Already existed: {existing}")
print(f"  Total: {added + existing}")
print("="*60 + "\n")

db.close()
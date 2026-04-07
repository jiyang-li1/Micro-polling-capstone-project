# test_search_by_district.py - Test district search functionality

from model_v2 import init_db, get_session, School, ZipCode, Poll, poll_zipcodes

engine = init_db('sqlite:///polling_v2.db')
db = get_session(engine)

print("\n" + "="*60)
print("Test District Search Functionality")
print("="*60)

# Input district name
district_query = input("\nEnter district name (e.g., Berkeley Unified): ").strip()

print(f"\nSearching: '{district_query}'")

# Step 1: Find district
print("\nStep 1: Find district...")
districts = db.query(School).filter(
    School.district.ilike(f'%{district_query}%'),
    School.record_type == 'District'
).all()

print(f"Found {len(districts)} district(s):")
for d in districts:
    print(f"  - {d.district}")

if not districts:
    print("\nError: No matching districts found!")
    db.close()
    exit()

# Use the first district
district = districts[0]
print(f"\nUsing district: {district.district}")

# Step 2: Get all zip codes for the district
print("\nStep 2: Get district zip codes...")
district_zipcodes = db.query(School.zip_code).filter(
    School.district == district.district,
    School.zip_code.isnot(None)
).distinct().all()

zipcodes = [zc[0] for zc in district_zipcodes]
print(f"District has {len(zipcodes)} zip code(s): {zipcodes[:10]}{'...' if len(zipcodes) > 10 else ''}")

# Step 3: Find these zip code IDs in the zipcodes table
print("\nStep 3: Look up zip code IDs in zipcodes table...")
zipcode_objs = db.query(ZipCode).filter(
    ZipCode.zip_code.in_(zipcodes)
).all()

zipcode_ids = [z.id for z in zipcode_objs]
print(f"Found {len(zipcode_ids)} zip code ID(s): {zipcode_ids}")

if not zipcode_ids:
    print("\nError: Zip codes not found in zipcodes table! Run fix_district_zipcodes.py")
    db.close()
    exit()

# Step 4: Find polls using these zip codes
print("\nStep 4: Find associated polls...")
poll_ids = db.query(poll_zipcodes.c.poll_id).filter(
    poll_zipcodes.c.zipcode_id.in_(zipcode_ids)
).distinct().all()

poll_id_list = [p[0] for p in poll_ids]
print(f"Found {len(poll_id_list)} poll ID(s): {poll_id_list}")

if not poll_id_list:
    print("\nError: No polls found using these zip codes!")
    print("Hint: Confirm whether the polls you created use these zip codes")
    db.close()
    exit()

# Step 5: Get poll details
print("\nStep 5: Get poll details...")
polls = db.query(Poll).filter(
    Poll.id.in_(poll_id_list),
    Poll.is_active == 1
).all()

print(f"\nFound {len(polls)} active poll(s):")
for poll in polls:
    print(f"  [{poll.id}] {poll.title}")
    # Show poll's zip codes
    poll_zips = [z.zip_code for z in poll.zipcodes]
    print(f"      Zip codes: {poll_zips[:5]}{'...' if len(poll_zips) > 5 else ''}")

print("\n" + "="*60)
db.close()
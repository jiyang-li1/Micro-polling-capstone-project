# debug_ravenswood.py - Debug Ravenswood District Polling

from model_v2 import init_db, get_session, Poll, School, poll_districts

engine = init_db('sqlite:///polling_v2.db')
db = get_session(engine)

print("\n" + "="*60)
print("Debug Ravenswood City Elementary District")
print("="*60)

district_name = "Ravenswood City Elementary"

# 1. Check if the district exists
print(f"\n1. Find district: {district_name}")
schools = db.query(School).filter(
    School.district.ilike(f'%{district_name}%')
).all()

print(f"   Found {len(schools)} record(s):")
for s in schools:
    print(f"   - ID: {s.id}, Type: {s.record_type}, District: {s.district}")

if not schools:
    print("\n   Error: District not found!")
    db.close()
    exit()

# Find District type records
district_records = [s for s in schools if s.record_type == 'District']
print(f"\n   Of which District type: {len(district_records)}")

if not district_records:
    print("   Error: No District type records found!")
    db.close()
    exit()

district = district_records[0]
print(f"   Using district ID: {district.id}")

# 2. Check associations in the poll_districts table
print(f"\n2. Check poll_districts association table")
links = db.query(poll_districts).filter(
    poll_districts.c.district_id == district.id
).all()

print(f"   Association record count: {len(links)}")
for link in links:
    print(f"   - Poll ID: {link.poll_id}, District ID: {link.district_id}")

if not links:
    print("\n   Error: No association records in poll_districts table!")
    print("   This means district association was not saved when creating the poll.")

# 3. View all polls
print(f"\n3. View all polls")
all_polls = db.query(Poll).all()
print(f"   Total polls: {len(all_polls)}")

for poll in all_polls:
    print(f"\n   Poll [{poll.id}]: {poll.title}")
    print(f"     Type: {poll.poll_type}")
    print(f"     Status: {'Active' if poll.is_active == 1 else 'Inactive'}")

    # Check district associations for this poll
    poll_districts_count = db.query(poll_districts).filter(
        poll_districts.c.poll_id == poll.id
    ).count()
    print(f"     Associated districts: {poll_districts_count}")

    if poll_districts_count > 0:
        district_links = db.query(poll_districts).filter(
            poll_districts.c.poll_id == poll.id
        ).all()
        for link in district_links:
            linked_district = db.query(School).filter_by(id=link.district_id).first()
            if linked_district:
                print(f"       - {linked_district.district}")

# 4. Check the most recently created poll
print(f"\n4. Most recently created poll")
recent_poll = db.query(Poll).order_by(Poll.created_at.desc()).first()
if recent_poll:
    print(f"   Latest poll [{recent_poll.id}]: {recent_poll.title}")
    print(f"   Created at: {recent_poll.created_at}")

    # Check its district associations
    districts_linked = recent_poll.districts
    print(f"   Associated districts: {len(districts_linked)}")
    for d in districts_linked:
        print(f"     - {d.district}")

print("\n" + "="*60)
db.close()
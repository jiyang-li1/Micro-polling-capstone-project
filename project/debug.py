# debug_ravenswood.py - Debug Ravenswood District Polling

from model_v2 import init_db, get_session, Poll, School, poll_districts

engine = init_db('sqlite:///polling_v2.db')
db = get_session(engine)

print("\n" + "="*60)
print("调试 Ravenswood City Elementary 学区")
print("="*60)

district_name = "Ravenswood City Elementary"

# 1. Check if the district exists
print(f"\n1. 查找学区: {district_name}")
schools = db.query(School).filter(
    School.district.ilike(f'%{district_name}%')
).all()

print(f"   找到 {len(schools)} 条记录:")
for s in schools:
    print(f"   - ID: {s.id}, Type: {s.record_type}, District: {s.district}")

if not schools:
    print("\n   问题：学区不存在！")
    db.close()
    exit()

# Find District type records
district_records = [s for s in schools if s.record_type == 'District']
print(f"\n   其中 District 类型: {len(district_records)}")

if not district_records:
    print("   问题：没有 District 类型的记录！")
    db.close()
    exit()

district = district_records[0]
print(f"   使用学区 ID: {district.id}")

# 2. Check associations in the poll_districts table
print(f"\n2. 检查 poll_districts 关联表")
links = db.query(poll_districts).filter(
    poll_districts.c.district_id == district.id
).all()

print(f"   关联记录数: {len(links)}")
for link in links:
    print(f"   - Poll ID: {link.poll_id}, District ID: {link.district_id}")

if not links:
    print("\n   问题：poll_districts 表中没有关联记录！")
    print("   这说明创建投票时，学区关联没有保存成功。")

# 3. View all polls
print(f"\n3. 查看所有投票")
all_polls = db.query(Poll).all()
print(f"   总投票数: {len(all_polls)}")

for poll in all_polls:
    print(f"\n   投票 [{poll.id}]: {poll.title}")
    print(f"     类型: {poll.poll_type}")
    print(f"     状态: {'Active' if poll.is_active == 1 else 'Inactive'}")
    
    # Check district associations for this poll
    poll_districts_count = db.query(poll_districts).filter(
        poll_districts.c.poll_id == poll.id
    ).count()
    print(f"     关联的学区数: {poll_districts_count}")
    
    if poll_districts_count > 0:
        district_links = db.query(poll_districts).filter(
            poll_districts.c.poll_id == poll.id
        ).all()
        for link in district_links:
            linked_district = db.query(School).filter_by(id=link.district_id).first()
            if linked_district:
                print(f"       - {linked_district.district}")

# 4. Check the most recently created poll
print(f"\n4. 最近创建的投票")
recent_poll = db.query(Poll).order_by(Poll.created_at.desc()).first()
if recent_poll:
    print(f"   最新投票 [{recent_poll.id}]: {recent_poll.title}")
    print(f"   创建时间: {recent_poll.created_at}")
    
    # Check its district associations
    districts_linked = recent_poll.districts
    print(f"   关联的学区数: {len(districts_linked)}")
    for d in districts_linked:
        print(f"     - {d.district}")

print("\n" + "="*60)
db.close()
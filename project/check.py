# test_search_by_district.py - Test district search functionality

from model_v2 import init_db, get_session, School, ZipCode, Poll, poll_zipcodes

engine = init_db('sqlite:///polling_v2.db')
db = get_session(engine)

print("\n" + "="*60)
print("测试学区搜索功能")
print("="*60)

# Input district name
district_query = input("\n输入学区名称（例如：Berkeley Unified）: ").strip()

print(f"\n搜索: '{district_query}'")

# Step 1: Find district
print("\n步骤1：查找学区...")
districts = db.query(School).filter(
    School.district.ilike(f'%{district_query}%'),
    School.record_type == 'District'
).all()

print(f"找到 {len(districts)} 个学区:")
for d in districts:
    print(f"  - {d.district}")

if not districts:
    print("\n问题：未找到匹配的学区！")
    db.close()
    exit()

# Use the first district
district = districts[0]
print(f"\n使用学区: {district.district}")

# Step 2: Get all zip codes for the district
print("\n步骤2：获取学区邮编...")
district_zipcodes = db.query(School.zip_code).filter(
    School.district == district.district,
    School.zip_code.isnot(None)
).distinct().all()

zipcodes = [zc[0] for zc in district_zipcodes]
print(f"学区有 {len(zipcodes)} 个邮编: {zipcodes[:10]}{'...' if len(zipcodes) > 10 else ''}")

# Step 3: Find these zip code IDs in the zipcodes table
print("\n步骤3：在 zipcodes 表中查找邮编 ID...")
zipcode_objs = db.query(ZipCode).filter(
    ZipCode.zip_code.in_(zipcodes)
).all()

zipcode_ids = [z.id for z in zipcode_objs]
print(f"找到 {len(zipcode_ids)} 个邮编 ID: {zipcode_ids}")

if not zipcode_ids:
    print("\n问题：邮编未在 zipcodes 表中！请运行 fix_district_zipcodes.py")
    db.close()
    exit()

# Step 4: Find polls using these zip codes
print("\n步骤4：查找关联的投票...")
poll_ids = db.query(poll_zipcodes.c.poll_id).filter(
    poll_zipcodes.c.zipcode_id.in_(zipcode_ids)
).distinct().all()

poll_id_list = [p[0] for p in poll_ids]
print(f"找到 {len(poll_id_list)} 个投票 ID: {poll_id_list}")

if not poll_id_list:
    print("\n问题：未找到使用这些邮编的投票！")
    print("提示：确认你创建的投票是否使用了这些邮编")
    db.close()
    exit()

# Step 5: Get poll details
print("\n步骤5：获取投票详情...")
polls = db.query(Poll).filter(
    Poll.id.in_(poll_id_list),
    Poll.is_active == 1
).all()

print(f"\n找到 {len(polls)} 个活跃的投票:")
for poll in polls:
    print(f"  [{poll.id}] {poll.title}")
    # Show poll's zip codes
    poll_zips = [z.zip_code for z in poll.zipcodes]
    print(f"      邮编: {poll_zips[:5]}{'...' if len(poll_zips) > 5 else ''}")

print("\n" + "="*60)
db.close()
# fix_district_zipcodes.py - 将 schools 表的邮编同步到 zipcodes 表

from model_v2 import init_db, get_session, School, ZipCode

engine = init_db('sqlite:///polling_v2.db')
db = get_session(engine)

print("\n" + "="*60)
print("同步学区邮编到 zipcodes 表")
print("="*60)

# 获取所有学区的邮编
school_zipcodes = db.query(
    School.zip_code,
    School.city,
    School.county
).filter(
    School.zip_code.isnot(None)
).distinct().all()

print(f"\n在 schools 表中找到 {len(school_zipcodes)} 个唯一邮编")

added = 0
existing = 0

for zip_code, city, county in school_zipcodes:
    # 检查是否已存在
    zc = db.query(ZipCode).filter_by(zip_code=zip_code).first()
    
    if not zc:
        # 创建新邮编
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
            print(f"已添加 {added} 个邮编...")
    else:
        existing += 1

db.commit()

print(f"\n完成！")
print(f"  新增邮编: {added}")
print(f"  已存在: {existing}")
print(f"  总计: {added + existing}")
print("="*60 + "\n")

db.close()
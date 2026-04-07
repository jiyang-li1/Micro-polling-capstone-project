# import_schools_v2.py - 导入学区数据到纯学区数据库

import pandas as pd
from models_school import init_db, get_session, School

print("\n" + "="*60)
print("导入学区数据到纯学区数据库")
print("="*60)

# 初始化数据库
engine = init_db('sqlite:///polling_v2.db')
db = get_session(engine)

# 清空旧数据
print("\n清空旧学区数据...")
db.query(School).delete()
db.commit()

# 读取 Excel 文件
excel_file = '../CDESchoolDirectoryExport.xlsx'
print(f"\n从 {excel_file} 读取数据...")

try:
    df = pd.read_excel(excel_file)
    df.dropna(how='all', inplace=True)  # 删除全空行
    print(f"✅ 读取到 {len(df)} 行数据")
    
    count = 0
    errors = 0
    
    for idx, row in df.iterrows():
        try:
            # 提取邮编（去掉后缀，如 94544-1136 -> 94544）
            zip_code = str(row['Street Zip']).split('-')[0] if pd.notna(row['Street Zip']) else None
            
            # 处理 "No Data"
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
            
            # 每1000条提交一次
            if count % 1000 == 0:
                db.commit()
                print(f"已导入 {count} 条...")
        
        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"错误（行 {idx+2}）: {e}")
    
    db.commit()
    
    print(f"\n✅ 成功导入 {count} 条学区/学校数据！")
    if errors > 0:
        print(f"⚠️  跳过了 {errors} 条错误数据")

except FileNotFoundError:
    print(f"\n❌ 错误：找不到文件 {excel_file}")
    print("请确保文件在项目根目录")
except Exception as e:
    print(f"\n❌ 导入失败：{e}")
    import traceback
    traceback.print_exc()
    db.rollback()

# 显示统计
print("\n" + "="*60)
print("数据统计：")
print("="*60)

total = db.query(School).count()
districts = db.query(School).filter_by(record_type='District').count()
schools = db.query(School).filter_by(record_type='School').count()
counties = db.query(School.county).distinct().count()
cities = db.query(School.city).distinct().count()
zips = db.query(School.zip_code).distinct().count()

print(f"总记录数: {total}")
print(f"  - 学区 (Districts): {districts}")
print(f"  - 学校 (Schools): {schools}")
print(f"县 (Counties): {counties}")
print(f"城市 (Cities): {cities}")
print(f"邮编 (Zip Codes): {zips}")

# 显示示例学区
print("\n示例学区（前10个）：")
sample_districts = db.query(School).filter_by(record_type='District').limit(10).all()
for s in sample_districts:
    print(f"  {s.district:50s} | {s.city:15s} | {s.county}")

print("="*60)

db.close()
print("\n✅ 导入完成！\n")
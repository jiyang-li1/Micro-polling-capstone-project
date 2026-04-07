# reset_database.py - Reset database, keeping only district data

import os
from model_v2 import init_db, Base, get_session, School

print("\n" + "="*60)
print("重置数据库")
print("="*60)

# Delete old database
db_file = 'polling_v2.db'
if os.path.exists(db_file):
    print(f"\n删除旧数据库: {db_file}")
    os.remove(db_file)
    print("删除成功")
else:
    print(f"\n数据库文件不存在: {db_file}")

# Create new database
print("\n创建新数据库...")
engine = init_db(f'sqlite:///{db_file}')

# Create all tables
Base.metadata.create_all(engine)
print("数据库表已创建")

# Verify tables
db = get_session(engine)

from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()

print("\n已创建的表:")
for table in tables:
    print(f"  - {table}")

# Check district data
school_count = db.query(School).count()
print(f"\n学区数据: {school_count} 条")

if school_count == 0:
    print("\n提示: 学区数据为空，请运行:")
    print("  python import_schools.py")

db.close()

print("\n" + "="*60)
print("数据库重置完成！")
print("="*60)

print("\n下一步:")
print("1. 运行: python import_schools.py  (导入学区数据)")
print("2. 运行: python create_admin_v2.py  (创建管理员账号)")
print("3. 运行: python app_v2.py  (启动应用)")
print()
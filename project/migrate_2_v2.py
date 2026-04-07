# migrate_add_poll_districts.py - Add poll_districts table

from model_v2 import init_db, Base, get_session, poll_districts
from sqlalchemy import inspect

print("\n" + "="*60)
print("添加 poll_districts 关联表")
print("="*60)

# Connect to database
engine = init_db('sqlite:///polling_v2.db')

# Check if table already exists
inspector = inspect(engine)
existing_tables = inspector.get_table_names()

print(f"\n当前表: {existing_tables}")

if 'poll_districts' in existing_tables:
    print("\npoll_districts 表已存在，无需创建")
else:
    print("\n创建 poll_districts 表...")
    # Only create this new table
    Base.metadata.tables['poll_districts'].create(engine)
    print("创建成功！")

# Verify
inspector = inspect(engine)
if 'poll_districts' in inspector.get_table_names():
    print("\n验证：poll_districts 表已创建")
    
    # Show table structure
    columns = inspector.get_columns('poll_districts')
    print("\n表结构:")
    for col in columns:
        print(f"  - {col['name']}: {col['type']}")
else:
    print("\n错误：表创建失败")

print("\n" + "="*60)
print("迁移完成！")
print("="*60 + "\n")
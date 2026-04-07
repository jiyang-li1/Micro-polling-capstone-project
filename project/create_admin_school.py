# create_admin_school.py - Create admin (school district version)

from models_school import init_db, get_session, Admin
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

print("\n" + "="*60)
print("创建管理员账户（学区投票系统）")
print("="*60 + "\n")

engine = init_db('sqlite:///polling_school.db')
db = get_session(engine)

username = input("输入管理员用户名: ").strip()
password = input("输入管理员密码: ").strip()

if not username or not password:
    print("\n❌ 用户名和密码不能为空！")
    exit(1)

# Check if already exists
existing = db.query(Admin).filter_by(username=username).first()
if existing:
    print(f"\n❌ 用户名 '{username}' 已存在！")
    db.close()
    exit(1)

# Create admin
admin = Admin(
    username=username,
    password_hash=hash_password(password)
)

db.add(admin)
db.commit()

print(f"\n✅ 管理员 '{username}' 创建成功！")
print("\n登录信息：")
print(f"  用户名: {username}")
print(f"  密码: {password}")
print("\n" + "="*60 + "\n")

db.close()
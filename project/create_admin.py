from model import init_db, get_session, Admin
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

engine = init_db('sqlite:///polling.db')
db = get_session(engine)



existing_admin = db.query(Admin).first()
if existing_admin:
    print(f"\n Existing admin: {existing_admin.username}")
    choice = input("Create a new admin? (y/n): ")
    if choice.lower() != 'y':
        db.close()
        exit()

print("\n Enter username and password:")
username = input("user name :").strip()
password = input("password : ").strip()

if not username or not password:
    print("Error: Username and password cannot be empty.")
    db.close()
    exit()

if db.query(Admin).filter_by(username=username).first():
    print(f"Admin '{username}' already exists")
    db.close()
    exit()

admin = Admin(
    username=username,
    password_hash=hash_password(password)
)

db.add(admin)
db.commit()

print(f"\n Created admin successfully!")
db.close()
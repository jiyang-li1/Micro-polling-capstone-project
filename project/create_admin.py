
from model import init_db, get_session, Admin
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

engine = init_db('sqlite:///polling_v2.db')
db = get_session(engine)
 

existing_admin = db.query(Admin).first()
if existing_admin:
    print(f"\n Admin exists: {existing_admin.username}")
    choice = input("Still create new admin? (y/n): ")
    if choice.lower() != 'y':
        print("Cancelled. No new admin created.")
        db.close()
        exit()


print("\nEnter username and password:")
username = input("Username: ").strip()
password = input("Password: ").strip()

if not username or not password:
    print("Error")
    db.close()
    exit()


if db.query(Admin).filter_by(username=username).first():
    print(f"'{username}' exists")
    db.close()
    exit()

admin = Admin(
    username=username,
    password_hash=hash_password(password)
)

db.add(admin)
db.commit()



db.close()
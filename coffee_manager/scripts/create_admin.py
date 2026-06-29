from coffee_manager.auth import hash_password
from coffee_manager.database import SessionLocal
from coffee_manager.models import User

db = SessionLocal()
try:
    if not db.query(User).filter(User.name == "admin").first():
        db.add(User(name="admin", password_hash=hash_password("admin")))
        db.commit()
        print("Created admin user (admin / admin)")
    else:
        print("Admin user already exists")
finally:
    db.close()

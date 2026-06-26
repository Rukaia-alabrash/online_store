from contextlib import contextmanager
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
from app.database import SessionLocal
from app.models.user import User, UserRole
from sqlalchemy.orm import Session
from passlib.context import CryptContext

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@contextmanager
def get_db_session():
    # Create a new database session for seeding data.
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def seed_user(db: Session):
    # Check if the user already exists to avoid duplicates.
    email = "user@test.com"
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return
    
    password = pwd_context.hash("user1234")

    user = User(
        name="user",
        email=email,
        password=password,
        role=UserRole.USER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    print(f"Created user_id={user.id}")


def main():
    # Seed the database with initial data.
    with get_db_session() as db:
        seed_user(db)


if __name__ == "__main__":
    main()

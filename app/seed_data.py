from alembic.migration import contextmanager
from dotenv import load_dotenv
from app.database import SessionLocal, get_db
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
    existing = db.query(User).filter(User.email == "rukaia@gmail.com").first()
    if existing:
        return
    
    password = pwd_context.hash("del1234")

    user = User(
        name="del",
        email="del@test.com",
        password=password,
        role=UserRole.ADMIN,
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

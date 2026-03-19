from app.database import get_db
from app.models.user import User, UserRole
from sqlalchemy.orm import Session
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def seed_user(db: Session):
    existing = db.query(User).filter(User.email=="rukaia@gmail.com").first()
    if existing:
        return
    password = pwd_context.hash("123")

    user = User(
        name="rukaia",
        email="rukaia@gmail.com",
        password=password,
        role=UserRole.USER
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    print(f"Created user_id={user.id}")


def main():
    # Create a database session and seed initial data.
    db = next(get_db())
    try:
        seed_user(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()

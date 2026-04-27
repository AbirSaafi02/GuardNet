from sqlalchemy.orm import Session

from backend.core.security import create_access_token, hash_password, verify_password
from backend.models.models import User
from backend.schemas.user import UserCreate, UserLogin


def register_user(db: Session, data: UserCreate):
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise ValueError("Email deja utilise")

    new_user = User(
        email=data.email,
        nom=data.nom,
        hashed_password=hash_password(data.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def login_user(db: Session, data: UserLogin):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise ValueError("Email ou mot de passe incorrect")
    return create_access_token(data={"sub": str(user.id), "user_id": user.id})

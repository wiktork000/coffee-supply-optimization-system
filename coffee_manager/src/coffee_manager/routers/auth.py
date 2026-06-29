from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from coffee_manager.auth import create_access_token, hash_password, verify_password
from coffee_manager.database import get_db
from coffee_manager.models import User
from coffee_manager.schemas import LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.name == body.username).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    return LoginResponse(
        token=create_access_token(str(user.id), user.role),
        user_id=user.id,
        role=user.role,
    )


@router.post(
    "/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED
)
def register(body: LoginRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.name == body.username).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username already taken"
        )
    user = User(name=body.username, password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return LoginResponse(
        token=create_access_token(str(user.id), user.role),
        user_id=user.id,
        role=user.role,
    )

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.db.database import get_session
from app.models import User
from app.schemas import SignUpRequest, LoginRequest, Token
from app.core.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=Token, status_code=201)
def signup(payload: SignUpRequest, session: Session = Depends(get_session)):
    if session.exec(select(User).where(User.username == payload.username)).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    if session.exec(select(User).where(User.email == payload.email)).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    user = User(
        username=payload.username,
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        birth_date=payload.birth_date,
        faculty_id=payload.faculty_id,
        year_of_study=payload.year_of_study,
        role_id=payload.role_id,
        hashed_password=hash_password(payload.password),
    )
    session.add(user)
    session.commit()
    token = create_access_token({"sub": user.username})
    return Token(access_token=token)


@router.post("/signin", response_model=Token)
def signin(creds: LoginRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == creds.email)).first()
    if not user or not verify_password(creds.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    token = create_access_token({"sub": user.username})
    return Token(access_token=token)

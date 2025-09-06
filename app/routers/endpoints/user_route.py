from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.models import get_session, User
from app.schemas import MeRead, MeUpdate
from app.core.deps import get_current_user
from app.core.security import verify_password, hash_password

router = APIRouter(prefix="/user", tags=["user"])


@router.get("", response_model=MeRead)
def get_me(current: User = Depends(get_current_user)):
    return MeRead(
        id=current.id,
        username=current.username,
        email=current.email,
        first_name=current.first_name,
        last_name=current.last_name,
        birth_date=current.birth_date,
        faculty_id=current.faculty_id,
        year_of_study=current.year_of_study,
    )


@router.put("", response_model=MeRead)
def update_me(
    payload: MeUpdate,
    current: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    # Check username uniqueness
    if payload.username and payload.username != current.username:
        if session.exec(select(User).where(User.username == payload.username)).first():
            raise HTTPException(status_code=400, detail="Username already exists")
        current.username = payload.username

    # Check email uniqueness
    if payload.email and payload.email != current.email:
        if session.exec(select(User).where(User.email == payload.email)).first():
            raise HTTPException(status_code=400, detail="Email already exists")
        current.email = payload.email

    # Update other fields
    if payload.first_name is not None:
        current.first_name = payload.first_name

    if payload.last_name is not None:
        current.last_name = payload.last_name

    if payload.birth_date is not None:
        current.birth_date = payload.birth_date

    if payload.faculty_id is not None:
        current.faculty_id = payload.faculty_id

    if payload.year_of_study is not None:
        current.year_of_study = payload.year_of_study

    # Update password if provided
    if payload.new_password is not None:
        current.hashed_password = hash_password(payload.new_password)

    session.add(current)
    session.commit()
    session.refresh(current)

    return MeRead(
        id=current.id,
        username=current.username,
        email=current.email,
        first_name=current.first_name,
        last_name=current.last_name,
        birth_date=current.birth_date,
        faculty_id=current.faculty_id,
        year_of_study=current.year_of_study,
    )

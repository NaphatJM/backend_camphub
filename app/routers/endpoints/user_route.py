from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from ....db.database import get_session
from ....models import User
from ....schemas import MeRead, MeUpdate
from ....core.deps import get_current_user
from ....core.security import verify_password, hash_password

router = APIRouter(prefix="/user", tags=["user"])


@router.get("", response_model=MeRead)
def get_me(current: User = Depends(get_current_user)):
    return MeRead(
        id=current.id,
        username=current.username,
        email=current.email,
        full_name=current.full_name,
    )


@router.put("", response_model=MeRead)
def update_me(
    payload: MeUpdate,
    current: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if payload.username and payload.username != current.username:
        exists = session.exec(
            select(User).where(User.username == payload.username)
        ).first()
        if exists:
            raise HTTPException(status_code=400, detail="Username already exists")
        current.username = payload.username

    if payload.email and payload.email != current.email:
        exists = session.exec(select(User).where(User.email == payload.email)).first()
        if exists:
            raise HTTPException(status_code=400, detail="Email already exists")
        current.email = payload.email

    if payload.full_name is not None:
        current.full_name = payload.full_name

    if payload.new_password is not None:
        current.hashed_password = hash_password(payload.new_password)

    session.add(current)
    session.commit()
    session.refresh(current)

    return MeRead(
        id=current.id,
        username=current.username,
        email=current.email,
        full_name=current.full_name,
    )

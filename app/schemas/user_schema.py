from typing import Optional
from datetime import date
from sqlmodel import SQLModel
from pydantic import computed_field


# Auth
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(SQLModel):
    email: str
    password: str


class SignUpRequest(SQLModel):
    username: str
    email: str
    password: str
    first_name: str
    last_name: str
    birth_date: date
    faculty_id: Optional[int] = None
    year_of_study: Optional[int] = None
    role_id: int = 2  # Default to student


# Me
class UserBase(SQLModel):
    id: int
    username: str
    first_name: str
    last_name: str


class UserSimple(UserBase):
    profile_image_url: Optional[str] = None
    pass


class MeRead(UserBase):
    email: str
    birth_date: date
    faculty_id: Optional[int] = None
    faculty_name: Optional[str] = None
    year_of_study: Optional[int] = None
    role_id: Optional[int] = None
    role_name: Optional[str] = None
    profile_image_url: Optional[str] = None

    @computed_field
    def age(self) -> Optional[int]:
        if not self.birth_date:
            return None
        today = date.today()
        return (
            today.year
            - self.birth_date.year
            - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        )

    @computed_field
    def fullname(self) -> str:
        return f"{self.first_name} {self.last_name}"


class MeUpdate(SQLModel):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    birth_date: Optional[date] = None
    faculty_id: Optional[int] = None
    role_id: Optional[int] = None
    year_of_study: Optional[int] = None
    new_password: Optional[str] = None
    profile_image_url: Optional[str] = None

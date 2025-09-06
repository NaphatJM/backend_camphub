from typing import Optional
from sqlmodel import SQLModel, Field, Column, String


class Role(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(sa_column=Column(String, unique=True, index=True, nullable=False))
    description: str = Field(sa_column=Column(String, nullable=False))

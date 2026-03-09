from datetime import datetime
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    role: str = "USER"


class UserOut(BaseModel):
    id: int
    name: str
    role: str

    class Config:
        from_attributes = True


class ResourceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)


class ResourceOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ReservationCreate(BaseModel):
    user_id: int
    resource_id: int
    start_at: datetime
    end_at: datetime


class ReservationOut(BaseModel):
    id: int
    user_id: int
    resource_id: int
    start_at: datetime
    end_at: datetime
    status: str

    class Config:
        from_attributes = True

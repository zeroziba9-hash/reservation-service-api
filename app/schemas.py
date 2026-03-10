from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    request_id: str | None = None


class SignupRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=4, max_length=64)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class ResourceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)


class ResourceUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=120)


class ResourceOut(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class DeleteOut(BaseModel):
    deleted: bool


class HealthOut(BaseModel):
    status: str


class ReadyOut(BaseModel):
    status: str
    db: str


class ReservationCreate(BaseModel):
    resource_id: int
    start_at: datetime
    end_at: datetime


class ReservationUpdate(BaseModel):
    start_at: datetime
    end_at: datetime


class ReservationOut(BaseModel):
    id: int
    user_id: int
    resource_id: int
    start_at: datetime
    end_at: datetime
    status: str
    resource_name: str | None = None
    user_email: EmailStr | None = None

    model_config = ConfigDict(from_attributes=True)

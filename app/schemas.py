from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, ConfigDict


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


class ResourceOut(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ReservationCreate(BaseModel):
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

    model_config = ConfigDict(from_attributes=True)

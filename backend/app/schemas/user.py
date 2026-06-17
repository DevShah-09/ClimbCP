import uuid
import re
from pydantic import BaseModel, Field, field_validator


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=6)
    codeforces_handle: str = Field(..., min_length=1)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        v = v.strip()
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, v):
            raise ValueError('Invalid email format')
        return v


class UserLogin(BaseModel):
    username: str = Field(..., description="Accepts username or email")
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    codeforces_handle: str

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

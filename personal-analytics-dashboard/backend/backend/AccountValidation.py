import re
from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional
from datetime import datetime


# Validation Rules
# Username: 3-20 characters, letters, numbers, and underscores only
# Email: Valid email format required
# Password: Minimum 8 characters, must include uppercase, lowercase, number, and special character
# Names: At least 2 characters, letters only
# Phone: Optional, must be at least 10 digits
# Bio: Optional, maximum 500 characters


class UserCreate(BaseModel):
    """Schema for creating a new user with validation rules"""
    
    username: str = Field(..., min_length=3, max_length=20)
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=2)
    last_name: str = Field(..., min_length=2)
    phone: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)
    
    @validator('username')
    def validate_username(cls, v):
        """Username must only contain letters, numbers, and underscores"""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        """Password must include uppercase, lowercase, number, and special character"""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', v):
            raise ValueError('Password must contain at least one special character')
        return v
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        """Names must contain only letters"""
        if not re.match(r'^[a-zA-Z]+$', v):
            raise ValueError('Names can only contain letters')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        """Phone must be at least 10 digits (if provided)"""
        if v is not None:
            # Remove common phone formatting characters
            digits_only = re.sub(r'[\D]', '', v)
            if len(digits_only) < 10:
                raise ValueError('Phone number must contain at least 10 digits')
        return v


class UserResponse(BaseModel):
    """Schema for returning user data (without password)"""
    
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    bio: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=2)
    last_name: Optional[str] = Field(None, min_length=2)
    phone: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        """Names must contain only letters"""
        if v is not None and not re.match(r'^[a-zA-Z]+$', v):
            raise ValueError('Names can only contain letters')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        """Phone must be at least 10 digits (if provided)"""
        if v is not None:
            digits_only = re.sub(r'[\D]', '', v)
            if len(digits_only) < 10:
                raise ValueError('Phone number must contain at least 10 digits')
        return v

"""
Pydantic 数据验证模型
"""
from pydantic import BaseModel, EmailStr, validator, field_validator
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """用户基础模型"""
    username: str
    email: EmailStr


class UserCreate(UserBase):
    """用户创建请求"""
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含数字')
        return v


class UserUpdate(BaseModel):
    """用户更新请求"""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None


class UserResponse(UserBase):
    """用户响应模型"""
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    """用户资料响应"""
    first_name: Optional[str]
    last_name: Optional[str]
    phone: Optional[str]
    avatar_url: Optional[str]
    
    class Config:
        from_attributes = True


class UserWithProfile(UserResponse):
    """带资料的用户响应"""
    profile: Optional[UserProfileResponse] = None


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """令牌响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class PasswordChange(BaseModel):
    """密码修改请求"""
    old_password: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含数字')
        return v


class PasswordResetRequest(BaseModel):
    """密码重置请求"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """密码重置确认"""
    token: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含数字')
        return v


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""
    refresh_token: str

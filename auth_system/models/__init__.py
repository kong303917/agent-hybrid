"""
数据模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    """用户模型"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 登录失败相关
    login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    
    # 关系
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    refresh_tokens = relationship("RefreshToken", back_populates="user")


class UserProfile(Base):
    """用户资料模型"""
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    phone = Column(String(20))
    avatar_url = Column(String(255))
    
    user = relationship("User", back_populates="profile")


class RefreshToken(Base):
    """刷新令牌模型"""
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    token = Column(String(500), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_revoked = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="refresh_tokens")


class Role(Base):
    """角色模型"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))


class UserRole(Base):
    """用户角色关联模型"""
    __tablename__ = "user_roles"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id"), primary_key=True)

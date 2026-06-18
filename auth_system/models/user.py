"""
用户模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime, nullable=True)
    login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User {self.username}>"

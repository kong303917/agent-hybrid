"""
用户认证系统配置
"""
import os
from datetime import timedelta

# JWT配置
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./auth.db")

# 密码策略
MIN_PASSWORD_LENGTH = 8
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15

# CORS配置
ALLOWED_ORIGINS = ["http://localhost:3000", "http://localhost:8080"]

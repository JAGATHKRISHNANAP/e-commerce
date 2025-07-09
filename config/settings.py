# config/settings.py - Simple Version (without pydantic-settings)

import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database
    db_name: str = os.getenv("DB_NAME", "e-commerce_second")
    db_user: str = os.getenv("DB_USER", "postgres")
    db_password: str = os.getenv("DB_PASSWORD", "jaTHU@12")
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: str = os.getenv("DB_PORT", "5432")
    
    # API Configuration
    api_v1_str: str = os.getenv("API_V1_STR", "/api/v1")
    project_name: str = os.getenv("PROJECT_NAME", "E-commerce API")
    
    # CORS
    backend_cors_origins: list = ["http://localhost:3000", "http://localhost:5173"]

settings = Settings()

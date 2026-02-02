# # import os
# # from pydantic import BaseSettings

# # class Settings(BaseSettings):
# #     # Database
# #     db_name: str = "datasource"
# #     db_user: str = "postgres"
# #     db_password: str = "jaTHU@12"
# #     db_host: str = "localhost"
# #     db_port: str = "5432"
    
# #     # API Configuration
# #     api_v1_str: str = "/api/v1"
# #     project_name: str = "E-commerce API"
    
# #     # CORS
# #     backend_cors_origins: list = ["http://localhost:3000", "http://localhost:5173"]
    
# #     class Config:
# #         env_file = ".env"

# # settings = Settings()


# # config/settings.py - Fixed Version

# # import os
# # from pydantic_settings import BaseSettings  # Changed import

# # class Settings(BaseSettings):
# #     # Database
# #     db_name: str = "datasource"
# #     db_user: str = "postgres"
# #     db_password: str = "jaTHU@12"
# #     db_host: str = "localhost"
# #     db_port: str = "5432"
    
# #     # API Configuration
# #     api_v1_str: str = "/api/v1"
# #     project_name: str = "E-commerce API"
    
# #     # CORS
# #     backend_cors_origins: list = ["http://localhost:3000", "http://localhost:5173"]
    
# #     class Config:
# #         env_file = ".env"

# # settings = Settings()


# config/settings.py - Simple Version (without pydantic-settings)

import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database
    db_name: str = os.getenv("DB_NAME", "e-commerce_second")
    db_user: str = os.getenv("DB_USER", "postgres")
    db_password: str = os.getenv("DB_PASSWORD", "jaTHU@12")
    db_host: str = os.getenv("DB_HOST", "65.1.248.179")
    db_port: str = os.getenv("DB_PORT", "5432")
    
    # API Configuration
    api_v1_str: str = os.getenv("API_V1_STR", "/api/v1")
    project_name: str = os.getenv("PROJECT_NAME", "E-commerce API")
    
    # CORS
    backend_cors_origins: list = ["http://localhost:3000", "http://localhost:5173"]

settings = Settings()


# # config/settings.py - Fixed version with Elasticsearch settings

# import os
# from dotenv import load_dotenv

# load_dotenv()

# class Settings:
#     # Database
#     db_name: str = os.getenv("DB_NAME", "e-commerce_second")
#     db_user: str = os.getenv("DB_USER", "postgres")
#     db_password: str = os.getenv("DB_PASSWORD", "jaTHU@12")
#     db_host: str = os.getenv("DB_HOST", "localhost")
#     db_port: str = os.getenv("DB_PORT", "5432")
    
#     # Elasticsearch - Add these missing settings
#     elasticsearch_host: str = os.getenv("ELASTICSEARCH_HOST", "localhost")
#     elasticsearch_port: int = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
#     elasticsearch_username: str = os.getenv("ELASTICSEARCH_USERNAME", "")
#     elasticsearch_password: str = os.getenv("ELASTICSEARCH_PASSWORD", "")
#     elasticsearch_use_ssl: bool = os.getenv("ELASTICSEARCH_USE_SSL", "false").lower() == "true"
#     elasticsearch_verify_certs: bool = os.getenv("ELASTICSEARCH_VERIFY_CERTS", "false").lower() == "true"
    
#     # API Configuration
#     api_v1_str: str = os.getenv("API_V1_STR", "/api/v1")
#     project_name: str = os.getenv("PROJECT_NAME", "E-commerce API")
    
#     # CORS
#     backend_cors_origins: list = ["http://localhost:3000", "http://localhost:5173"]

# settings = Settings()
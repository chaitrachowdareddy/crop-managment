"""
Configuration file for the Crop Supply Chain Management System.
Loads environment variables from .env if available, or falls back to sensible defaults.
"""
import os
import secrets
from dotenv import load_dotenv

# Load variables from .env file into environment
load_dotenv()

class Config:
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY') or secrets.token_hex(32)
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() in ('true', '1', 't')

# MySQL Database connection parameters
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', '3306'))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'crop_management')
    
    @classmethod
    def get_db_config(cls):
        """Returns database configuration dictionary for mysql-connector / pymysql."""
        return {
            'host': cls.DB_HOST,
            'port': cls.DB_PORT,
            'user': cls.DB_USER,
            'password': cls.DB_PASSWORD,
            'database': cls.DB_NAME,
        }

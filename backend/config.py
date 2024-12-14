import os
from dotenv import load_dotenv
from pathlib import Path

# Load appropriate .env file based on environment
def load_environment():
    env = os.getenv('NODE_ENV', 'development')
    env_file = f'.env.{env}' if env != 'development' else '.env'
    
    if os.path.exists(env_file):
        load_dotenv(env_file)
    else:
        load_dotenv()

load_environment()

# Base directory of the backend
BASE_DIR = Path(__file__).resolve().parent

# Core Configuration
class Config:
    # Environment
    ENV = os.getenv('NODE_ENV', 'development')
    DEBUG = ENV == 'development'
    
    # Server
    PORT = int(os.getenv('PORT', 5000))
    HOST = os.getenv('HOST', '0.0.0.0')
    API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000')
    
    # CORS
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173').split(',')
    
    # Reddit API
    REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
    REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
    REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT', 'DownvoteAnalyzer/1.0')
    
    # Database
    DB_PATH = os.getenv('DB_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reddit_downvotes.db'))
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', 100))
    RATE_LIMIT_PER_HOUR = int(os.getenv('RATE_LIMIT_PER_HOUR', 1000))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'downvoter.log')
    LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', 1048576))
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', 7))
    
    # Collection Settings
    COLLECTION_WINDOW_HOURS = int(os.getenv('COLLECTION_WINDOW_HOURS', 24))
    COLLECTION_DELAY_HOURS = int(os.getenv('COLLECTION_DELAY_HOURS', 2))
    COLLECTION_TIME_UTC = int(os.getenv('COLLECTION_TIME_UTC', 21))
    
    # Email Settings
    ALERT_EMAIL = os.getenv('ALERT_EMAIL')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

    @classmethod
    def is_production(cls):
        return cls.ENV == 'production'
    
    @classmethod
    def is_development(cls):
        return cls.ENV == 'development'
    
    @classmethod
    def is_staging(cls):
        return cls.ENV == 'staging'

config = Config()
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus, urlparse
import logging

logger = logging.getLogger(__name__)

# Load environment file first
def load_environment():
    env = os.getenv('NODE_ENV', 'production')  # Default to production
    env_file = f'.env.{env}'
    
    if os.path.exists(env_file):
        logger.info(f"Loading environment from {env_file}")
        load_dotenv(env_file)
        return True
    else:
        logger.warning(f"Environment file {env_file} not found")
        return False

# Load environment before config initialization
load_environment()

class Config:
    def __init__(self):
        # Base configuration
        self.ENV = os.getenv('NODE_ENV', 'development')
        self.DEBUG = self.ENV == 'development'

    # Add Reddit API Settings
        self.REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
        if not self.REDDIT_CLIENT_ID:
            raise ValueError("REDDIT_CLIENT_ID environment variable is not set")
        
        self.REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
        if not self.REDDIT_CLIENT_SECRET:
            raise ValueError("REDDIT_CLIENT_SECRET environment variable is not set")
        
        self.REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT', 'DownvoteAnalyzer/1.0')
    
                # Server settings
        self.PORT = int(os.getenv('PORT', 5000))
        self.HOST = os.getenv('HOST', '0.0.0.0')  # Added this line back
        
        # Database URL parsing and validation
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is not set")
            
        # Parse and validate database URL
        try:
            parsed_url = urlparse(database_url)
            
            # Store parsed components
            self.DB_USER = parsed_url.username
            self.DB_PASS = parsed_url.password
            self.DB_HOST = parsed_url.hostname
            self.DB_PORT = parsed_url.port
            self.DB_NAME = parsed_url.path[1:]  # Remove leading slash
            
            # Create properly encoded URL
            self.DATABASE_URL = (
                f"postgresql://{self.DB_USER}:{quote_plus(self.DB_PASS)}"
                f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
                "?sslmode=require"
            )
            
            logger.info(f"Database configured for host: {self.DB_HOST}")
            
        except Exception as e:
            logger.error(f"Failed to parse DATABASE_URL: {str(e)}")
            raise
        
        # Rate Limiting
        self.RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', 100))
        self.RATE_LIMIT_PER_HOUR = int(os.getenv('RATE_LIMIT_PER_HOUR', 1000))
        
        # Logging
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.LOG_FILE = os.getenv('LOG_FILE', 'downvoter.log')
        self.LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', 1048576))
        self.LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', 7))
        
        # Collection Settings
        self.COLLECTION_WINDOW_HOURS = int(os.getenv('COLLECTION_WINDOW_HOURS', 24))
        self.COLLECTION_DELAY_HOURS = int(os.getenv('COLLECTION_DELAY_HOURS', 2))
        self.COLLECTION_TIME_UTC = int(os.getenv('COLLECTION_TIME_UTC', 21))
        
        # Email Settings
        self.ALERT_EMAIL = os.getenv('ALERT_EMAIL')
        self.EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

    @classmethod
    def is_production(cls):
        return os.getenv('NODE_ENV') == 'production'
    
    @classmethod
    def is_development(cls):
        return os.getenv('NODE_ENV') == 'development'
    
    @classmethod
    def is_staging(cls):
        return os.getenv('NODE_ENV') == 'staging'

# Create config instance
config = Config()
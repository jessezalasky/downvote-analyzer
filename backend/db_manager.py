import psycopg2
from psycopg2 import pool
import logging
import time
from contextlib import contextmanager
from typing import Optional

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and connection pool"""
    
    def __init__(self, config):
        self.config = config
        self._pool: Optional[pool.SimpleConnectionPool] = None
        self.min_connections = 1
        self.max_connections = 5
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        
    def _create_pool(self) -> None:
        """Creates the connection pool with the configured settings"""
        try:
            logger.info("Initializing database connection pool...")
            self._pool = pool.SimpleConnectionPool(
                minconn=self.min_connections,
                maxconn=self.max_connections,
                dsn=self.config.DATABASE_URL,
                # Connection settings
                connect_timeout=30,
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=5
            )
            logger.info("Database connection pool initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to create connection pool: {str(e)}")
            raise
    
    @contextmanager
    def get_connection(self):
        """
        Gets a connection from the pool with automatic cleanup.
        Usage:
            with db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
        """
        conn = None
        retry_count = 0
        
        while retry_count < self.max_retries:
            try:
                # Create pool if it doesn't exist
                if self._pool is None:
                    self._create_pool()
                
                # Get connection from pool
                conn = self._pool.getconn()
                conn.autocommit = False  # Explicit transaction management
                
                # Test the connection
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                
                logger.debug("Successfully acquired database connection")
                yield conn
                return
                
            except Exception as e:
                retry_count += 1
                logger.warning(f"Connection attempt {retry_count} failed: {str(e)}")
                
                if conn:
                    try:
                        self._pool.putconn(conn)
                    except Exception:
                        pass
                    
                if retry_count == self.max_retries:
                    logger.error("Max retries reached, unable to establish connection")
                    raise
                    
                time.sleep(self.retry_delay * retry_count)  # Exponential backoff
                
        raise Exception("Failed to get database connection after all retries")
    
    def close_pool(self):
        """Closes all connections in the pool"""
        if self._pool is not None:
            logger.info("Closing database connection pool")
            self._pool.closeall()
            self._pool = None

# Example usage:
# db_manager = DatabaseManager(config)
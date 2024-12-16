import logging
from config import Config
from db_manager import DatabaseManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test database connectivity and basic operations"""
    config = Config()
    db_manager = DatabaseManager(config)
    
    try:
        # Test basic connection
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Test query
                cur.execute("SELECT version()")
                version = cur.fetchone()[0]
                logger.info(f"Connected to: {version}")
                
                # Test table creation
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS connection_test (
                        id serial PRIMARY KEY,
                        test_date timestamp DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                
                # Test insert
                cur.execute("INSERT INTO connection_test DEFAULT VALUES RETURNING id")
                new_id = cur.fetchone()[0]
                conn.commit()
                
                logger.info(f"Successfully created test record with ID: {new_id}")
                
        logger.info("All database tests passed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Database test failed: {str(e)}")
        return False
    finally:
        db_manager.close_pool()

if __name__ == "__main__":
    test_database_connection()
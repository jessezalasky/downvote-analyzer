import psycopg2
from psycopg2 import pool
import logging
from datetime import datetime
from config import config

logger = logging.getLogger(__name__)

class DatabaseManager:
    _instance = None
    
    def __init__(self):
        self.pool = None
        self.min_connections = 1
        self.max_connections = 5
        
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
        
    def initialize_pool(self):
        """Initialize the connection pool"""
        if self.pool is None:
            try:
                self.pool = psycopg2.pool.SimpleConnectionPool(
                    minconn=self.min_connections,
                    maxconn=self.max_connections,
                    dsn=config.DATABASE_URL
                )
                logger.info("Database pool initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize connection pool: {str(e)}")
                raise
    
    def get_connection(self):
        """Get a connection from the pool"""
        if self.pool is None:
            self.initialize_pool()
        return self.pool.getconn()
    
    def return_connection(self, conn):
        """Return a connection to the pool"""
        if self.pool is not None:
            self.pool.putconn(conn)

# Create global database manager instance
db_manager = DatabaseManager.get_instance()

def init_db():
    """Initialize the database with required tables"""
    conn = db_manager.get_connection()
    try:
        with conn.cursor() as cur:
            # Create daily champions table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS daily_champions (
                    id SERIAL PRIMARY KEY,
                    comment_id TEXT NOT NULL,
                    subreddit TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    body TEXT NOT NULL,
                    author TEXT NOT NULL,
                    permalink TEXT NOT NULL,
                    submission_title TEXT NOT NULL,
                    created_utc TIMESTAMP NOT NULL,
                    recorded_date DATE NOT NULL,
                    UNIQUE(subreddit, comment_id, recorded_date)
                )
            ''')

            # Create all-time champion table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS all_time_champion (
                    id SERIAL PRIMARY KEY,
                    comment_id TEXT NOT NULL,
                    subreddit TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    body TEXT NOT NULL,
                    author TEXT NOT NULL,
                    permalink TEXT NOT NULL,
                    submission_title TEXT NOT NULL,
                    created_utc TIMESTAMP NOT NULL,
                    recorded_date DATE NOT NULL
                )
            ''')

            # Create historical data table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS subreddit_historical_data (
                    id SERIAL PRIMARY KEY,
                    subreddit TEXT NOT NULL,
                    collection_date DATE NOT NULL,
                    downvoted_comments INTEGER NOT NULL,
                    total_downvotes INTEGER NOT NULL,
                    total_comments INTEGER NOT NULL,
                    UNIQUE(subreddit, collection_date)
                )
            ''')
            
        conn.commit()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to initialize database: {str(e)}")
        raise
    finally:
        db_manager.return_connection(conn)

def store_daily_champion(comment_data):
    """Store a daily champion in the database"""
    conn = db_manager.get_connection()
    try:
        with conn.cursor() as cur:
            created_utc = comment_data['created_utc'].isoformat() if isinstance(comment_data['created_utc'], datetime) else comment_data['created_utc']
            recorded_date = datetime.now().date().isoformat()
            
            cur.execute('''
                INSERT INTO daily_champions 
                (comment_id, subreddit, score, body, author, permalink, submission_title, created_utc, recorded_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (subreddit, comment_id, recorded_date) DO NOTHING
            ''', (
                comment_data['comment_id'],
                comment_data['subreddit'],
                comment_data['score'],
                comment_data['body'],
                comment_data['author'],
                comment_data['permalink'],
                comment_data['submission_title'],
                created_utc,
                recorded_date
            ))
            conn.commit()
            logger.info(f"Stored daily champion for r/{comment_data['subreddit']}")
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to store daily champion: {str(e)}")
        raise
    finally:
        db_manager.return_connection(conn)

def get_all_time_champion():
    """Fetch the all-time champion from the database"""
    conn = db_manager.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM all_time_champion ORDER BY score ASC LIMIT 1')
            result = cur.fetchone()
            
            if result:
                columns = ['id', 'comment_id', 'subreddit', 'score', 'body', 'author', 
                          'permalink', 'submission_title', 'created_utc', 'recorded_date']
                return dict(zip(columns, result))
            return None
    except Exception as e:
        logger.error(f"Failed to fetch all-time champion: {str(e)}")
        raise
    finally:
        db_manager.return_connection(conn)

def get_subreddit_historical_totals():
    """Get historical totals for all subreddits"""
    conn = db_manager.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('''
                SELECT 
                    subreddit,
                    SUM(total_downvotes) as all_time_downvotes,
                    SUM(total_comments) as all_time_comments,
                    MAX(collection_date) as last_updated
                FROM subreddit_historical_data
                GROUP BY subreddit
                ORDER BY all_time_downvotes ASC
            ''')
            results = cur.fetchall()
            
            return [{
                'subreddit': row[0],
                'all_time_downvotes': row[1],
                'all_time_comments': row[2],
                'last_updated': row[3]
            } for row in results]
    except Exception as e:
        logger.error(f"Failed to fetch historical totals: {str(e)}")
        raise
    finally:
        db_manager.return_connection(conn)

def get_all_time_champion():
    """Fetch the all-time champion from the database"""
    conn = db_manager.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM all_time_champion LIMIT 1')
            result = cur.fetchone()
            
            if result:
                # Return in the expected dictionary format
                return {
                    'comment_id': result[1],
                    'subreddit': result[2],
                    'score': result[3],
                    'body': result[4],
                    'author': result[5],
                    'permalink': result[6],
                    'submission_title': result[7],
                    'created_utc': result[8],
                    'recorded_date': result[9]
                }
            return None
    except Exception as e:
        logger.error(f"Error fetching all-time champion: {str(e)}")
        raise
    finally:
        db_manager.return_connection(conn)

def store_daily_champion(comment_data):
    """Store a daily champion in the database"""
    conn = db_manager.get_connection()
    try:
        with conn.cursor() as cur:
            # Convert datetime objects to strings
            created_utc = comment_data['created_utc'].isoformat() if isinstance(comment_data['created_utc'], datetime) else comment_data['created_utc']
            recorded_date = datetime.now().date().isoformat()
            
            cur.execute('''
                INSERT INTO daily_champions 
                (comment_id, subreddit, score, body, author, permalink, 
                 submission_title, created_utc, recorded_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (subreddit, comment_id, recorded_date) DO NOTHING
            ''', (
                comment_data['comment_id'],
                comment_data['subreddit'],
                comment_data['score'],
                comment_data['body'],
                comment_data['author'],
                comment_data['permalink'],
                comment_data['submission_title'],
                created_utc,
                recorded_date
            ))
            conn.commit()
            logger.info(f"Successfully stored daily champion for r/{comment_data['subreddit']}")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error storing daily champion: {str(e)}")
        raise
    finally:
        db_manager.return_connection(conn)

def store_subreddit_totals(subreddit, total_downvotes, total_comments):
    """Store daily totals for a subreddit"""
    conn = db_manager.get_connection()
    try:
        with conn.cursor() as cur:
            collection_date = datetime.now().date().isoformat()
            
            # Store in historical data
            cur.execute('''
                INSERT INTO subreddit_historical_data
                (subreddit, collection_date, downvoted_comments, total_downvotes, total_comments)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (subreddit, collection_date) 
                DO UPDATE SET
                    downvoted_comments = EXCLUDED.downvoted_comments,
                    total_downvotes = EXCLUDED.total_downvotes,
                    total_comments = EXCLUDED.total_comments
            ''', (
                subreddit,
                collection_date,
                total_comments,  # downvoted_comments count
                total_downvotes,
                total_comments
            ))
            conn.commit()
            logger.info(f"Successfully stored totals for r/{subreddit}")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error storing subreddit totals: {str(e)}")
        raise
    finally:
        db_manager.return_connection(conn)

def get_stored_daily_champion(subreddit):
    """Get most recent daily champion for a subreddit"""
    conn = db_manager.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('''
                SELECT * FROM daily_champions 
                WHERE subreddit = %s
                ORDER BY recorded_date DESC, score ASC
                LIMIT 1
            ''', (subreddit,))
            
            result = cur.fetchone()
            
            if result:
                return {
                    'comment_id': result[1],
                    'subreddit': result[2],
                    'score': result[3],
                    'body': result[4],
                    'author': result[5],
                    'permalink': result[6],
                    'submission_title': result[7],
                    'created_utc': result[8],
                    'recorded_date': result[9]
                }
            return None
    except Exception as e:
        logger.error(f"Error getting stored daily champion for r/{subreddit}: {str(e)}")
        raise
    finally:
        db_manager.return_connection(conn)

def update_all_time_champion(comment_data):
    """Update all-time champion if this comment has more downvotes"""
    logger.info(f"Checking all-time champion against score: {comment_data['score']}")
    
    conn = db_manager.get_connection()
    try:
        with conn.cursor() as cur:
            # Convert datetime objects to strings
            created_utc = comment_data['created_utc'].isoformat() if isinstance(comment_data['created_utc'], datetime) else comment_data['created_utc']
            recorded_date = datetime.now().date().isoformat()

            # Get current champion's score
            cur.execute('SELECT score FROM all_time_champion LIMIT 1')
            current_champion = cur.fetchone()

            if not current_champion or comment_data['score'] < current_champion[0]:
                logger.info(f"New all-time champion found! Score: {comment_data['score']}")

                # Delete old champion and insert new one
                cur.execute('TRUNCATE TABLE all_time_champion')
                cur.execute('''
                    INSERT INTO all_time_champion 
                    (comment_id, subreddit, score, body, author, permalink, 
                     submission_title, created_utc, recorded_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    comment_data['comment_id'],
                    comment_data['subreddit'],
                    comment_data['score'],
                    comment_data['body'],
                    comment_data['author'],
                    comment_data['permalink'],
                    comment_data['submission_title'],
                    created_utc,
                    recorded_date
                ))
                logger.info("All-time champion updated successfully")
            else:
                logger.info("No new all-time champion - current record stands")

        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to update all-time champion: {str(e)}")
        raise
    finally:
        db_manager.return_connection(conn)

def get_subreddit_historical_totals():
    """Get historical totals for all subreddits"""
    conn = db_manager.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('''
                SELECT 
                    subreddit,
                    SUM(total_downvotes) as all_time_downvotes,
                    SUM(total_comments) as all_time_comments,
                    COUNT(DISTINCT collection_date) as days_collected,
                    MAX(collection_date) as last_updated
                FROM subreddit_historical_data
                GROUP BY subreddit
                ORDER BY all_time_downvotes ASC
            ''')
            
            results = cur.fetchall()
            
            return [{
                'subreddit': row[0],
                'all_time_downvotes': row[1],
                'all_time_comments': row[2],
                'days_collected': row[3],
                'last_updated': row[4]
            } for row in results]
    except Exception as e:
        logger.error(f"Error fetching historical totals: {str(e)}")
        raise
    finally:
        db_manager.return_connection(conn)

def test_database_connection():
    """Test database connectivity"""
    logger.info("Testing database connection...")
    conn = db_manager.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT version()')
            version = cur.fetchone()[0]
            logger.info(f"Successfully connected to PostgreSQL: {version}")
            return True
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return False
    finally:
        db_manager.return_connection(conn)
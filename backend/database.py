from datetime import datetime
import logging
from psycopg2 import pool
from psycopg2.extras import DictCursor
import psycopg2
from config import config
logger = logging.getLogger(__name__)

# Global connection pool
db_pool = None

def get_db_pool():
    """Initialize or return existing connection pool"""
    global db_pool
    if db_pool is None:
        try:
            db_pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=config.DATABASE_URL
            )
            logger.info("Database pool created successfully")
        except psycopg2.Error as e:
            logger.error(f"Error creating database pool: {str(e)}")
            raise
    return db_pool

def init_db():
    """Initialize the database with required tables"""
    try:
        pool = get_db_pool()
        conn = pool.getconn()
        c = conn.cursor()
        
        # Create daily champions table
        c.execute('''
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
        c.execute('''
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

        # Create all-time subreddit totals table
        c.execute('''
            CREATE TABLE IF NOT EXISTS all_time_subreddit_totals (
                id SERIAL PRIMARY KEY,
                subreddit TEXT NOT NULL UNIQUE,
                total_downvotes INTEGER NOT NULL,
                total_comments INTEGER NOT NULL,
                last_updated TIMESTAMP NOT NULL
            )
        ''')

        # Create historical data table
        c.execute('''
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
    except psycopg2.Error as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise
    finally:
        if conn:
            pool.putconn(conn)

def store_daily_champion(comment_data):
    """Store a daily champion in the database"""
    pool = get_db_pool()
    conn = pool.getconn()
    
    try:
        with conn.cursor() as c:
            # Convert datetime objects to strings
            created_utc = comment_data['created_utc'].isoformat() if isinstance(comment_data['created_utc'], datetime) else comment_data['created_utc']
            recorded_date = datetime.now().date().isoformat()
            
            # Log before insert
            logger.info(f"Inserting record with date: {recorded_date}")
            
            c.execute('''
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
            logger.info(f"Successfully stored record for r/{comment_data['subreddit']}")
            
    except psycopg2.Error as e:
        logger.error(f"Failed to store record: {str(e)}")
        raise
    finally:
        pool.putconn(conn)

def update_all_time_champion(comment_data):
    """Update all-time champion if this comment has more downvotes"""
    logger.info(f"Checking all-time champion against score: {comment_data['score']}")
    
    pool = get_db_pool()
    conn = pool.getconn()

    try:
        with conn.cursor() as c:
            # Convert datetime objects to strings
            created_utc = comment_data['created_utc'].isoformat() if isinstance(comment_data['created_utc'], datetime) else comment_data['created_utc']
            recorded_date = datetime.now().date().isoformat()

            # Get current champion's score
            c.execute('SELECT score FROM all_time_champion LIMIT 1')
            current_champion = c.fetchone()

            if not current_champion or comment_data['score'] < current_champion[0]:
                logger.info(f"New all-time champion found! Score: {comment_data['score']}")

                # Delete old champion and insert new one
                c.execute('TRUNCATE TABLE all_time_champion')  # PostgreSQL's TRUNCATE is faster than DELETE
                c.execute('''
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
    except psycopg2.Error as e:
        logger.error(f"Error updating all-time champion: {str(e)}")
        raise
    finally:
        pool.putconn(conn)

def store_subreddit_historical_data(subreddit, data):
    """Store daily collection data in historical record"""
    logger.info(f"Storing historical data for r/{subreddit}")
    
    pool = get_db_pool()
    conn = pool.getconn()
    
    collection_date = datetime.now().date().isoformat()
    
    try:
        with conn.cursor() as c:
            c.execute('''
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
                data['downvoted_comments'],
                data['total_downvotes'],
                data['total_comments']
            ))
            
            conn.commit()
            logger.info(f"Successfully stored historical data for r/{subreddit}")
            
    except psycopg2.Error as e:
        logger.error(f"Failed to store historical data for r/{subreddit}: {str(e)}")
        raise
    finally:
        pool.putconn(conn)

def get_all_time_champion():
    """Fetch the all-time champion from the database"""
    logger.info("Fetching all-time champion")
    
    pool = get_db_pool()
    conn = pool.getconn()
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as c:
            c.execute('SELECT * FROM all_time_champion LIMIT 1')
            result = c.fetchone()

            if result:
                logger.info(f"All-time champion found with score: {result['score']}")
                return {
                    'comment_id': result['comment_id'],
                    'subreddit': result['subreddit'],
                    'score': result['score'],
                    'body': result['body'],
                    'author': result['author'],
                    'permalink': result['permalink'],
                    'submission_title': result['submission_title'],
                    'created_utc': result['created_utc'],
                    'recorded_date': result['recorded_date']
                }
            logger.info("No all-time champion found")
            return None
    except psycopg2.Error as e:
        logger.error(f"Error fetching all-time champion: {str(e)}")
        raise
    finally:
        pool.putconn(conn)

def store_subreddit_totals(subreddit, total_downvotes, total_comments):
    """Store daily totals for a subreddit in the database"""
    logger.info(f"Storing daily totals for r/{subreddit}")
    
    pool = get_db_pool()
    conn = pool.getconn()
    
    recorded_date = datetime.now().date().isoformat()
    
    try:
        with conn.cursor() as c:
            # Store in historical data
            data = {
                'downvoted_comments': total_comments,  # This is count of downvoted comments
                'total_downvotes': total_downvotes,
                'total_comments': total_comments
            }
            store_subreddit_historical_data(subreddit, data)
            
            # Update all_time_subreddit_totals for backward compatibility
            c.execute('''
                INSERT INTO all_time_subreddit_totals 
                (subreddit, total_downvotes, total_comments, last_updated)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (subreddit) 
                DO UPDATE SET
                    total_downvotes = EXCLUDED.total_downvotes,
                    total_comments = EXCLUDED.total_comments,
                    last_updated = EXCLUDED.last_updated
            ''', (
                subreddit,
                total_downvotes,
                total_comments,
                recorded_date
            ))
            
            conn.commit()
            logger.info(f"Successfully stored totals for r/{subreddit}")
            
    except psycopg2.Error as e:
        logger.error(f"Failed to store totals: {str(e)}")
        raise
    finally:
        pool.putconn(conn)

def get_subreddit_historical_totals():
    """Get historical totals for all subreddits"""
    logger.info("Fetching subreddit historical totals")
    
    pool = get_db_pool()
    conn = pool.getconn()
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as c:
            c.execute('''
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
            
            results = c.fetchall()
            return [dict(row) for row in results]
    except psycopg2.Error as e:
        logger.error(f"Error fetching historical totals: {str(e)}")
        raise
    finally:
        pool.putconn(conn)

def get_stored_daily_champion(subreddit):
    """Get today's champion from database for given subreddit"""
    pool = get_db_pool()
    conn = pool.getconn()
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as c:
            c.execute('''
                SELECT * FROM daily_champions 
                WHERE subreddit = %s
                ORDER BY id DESC LIMIT 1
            ''', (subreddit,))
            
            result = c.fetchone()
            
            if result:
                return {
                    'comment_id': result['comment_id'],
                    'subreddit': result['subreddit'],
                    'score': result['score'],
                    'body': result['body'],
                    'author': result['author'],
                    'permalink': result['permalink'],
                    'submission_title': result['submission_title'],
                    'created_utc': result['created_utc'],
                    'recorded_date': result['recorded_date']
                }
            return None
    except psycopg2.Error as e:
        logger.error(f"Error getting stored daily champion: {str(e)}")
        raise
    finally:
        pool.putconn(conn)
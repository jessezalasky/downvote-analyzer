import sqlite3
from datetime import datetime
import logging
from config import config
logger = logging.getLogger(__name__)

def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    
    try:
        # Create daily champions table
        c.execute('''
            CREATE TABLE IF NOT EXISTS daily_champions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comment_id TEXT NOT NULL,
                subreddit TEXT NOT NULL,
                score INTEGER NOT NULL,
                body TEXT NOT NULL,
                author TEXT NOT NULL,
                permalink TEXT NOT NULL,
                submission_title TEXT NOT NULL,
                created_utc TEXT NOT NULL,
                recorded_date TEXT NOT NULL,
                UNIQUE(subreddit, comment_id, recorded_date)
            )
        ''')

        # Create all-time champion table
        c.execute('''
            CREATE TABLE IF NOT EXISTS all_time_champion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comment_id TEXT NOT NULL,
                subreddit TEXT NOT NULL,
                score INTEGER NOT NULL,
                body TEXT NOT NULL,
                author TEXT NOT NULL,
                permalink TEXT NOT NULL,
                submission_title TEXT NOT NULL,
                created_utc TEXT NOT NULL,
                recorded_date TEXT NOT NULL
            )
        ''')

        # Create all-time subreddit totals table
        c.execute('''
            CREATE TABLE IF NOT EXISTS all_time_subreddit_totals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subreddit TEXT NOT NULL UNIQUE,
                total_downvotes INTEGER NOT NULL,
                total_comments INTEGER NOT NULL,
                last_updated TEXT NOT NULL
            )
        ''')

        # Create new historical data table
        c.execute('''
            CREATE TABLE IF NOT EXISTS subreddit_historical_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subreddit TEXT NOT NULL,
                collection_date DATE NOT NULL,
                downvoted_comments INTEGER NOT NULL,
                total_downvotes INTEGER NOT NULL,
                total_comments INTEGER NOT NULL,
                UNIQUE(subreddit, collection_date)
            )
        ''')
        
        conn.commit()
        logger.info("Database initialization successful")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise
    finally:
        conn.close()

def store_daily_champion(comment_data):
    """Store a daily champion in the database"""
    conn = sqlite3.connect(config.DB_PATH)
    conn.text_factory = str  # Add this line to handle Unicode
    c = conn.cursor()
    
    # Convert datetime objects to strings
    created_utc = comment_data['created_utc'].isoformat() if isinstance(comment_data['created_utc'], datetime) else comment_data['created_utc']
    recorded_date = datetime.now().date().isoformat()
    
    # Log before insert
    logger.info(f"Inserting record with date: {recorded_date}")
    
    try:
        c.execute('''
            INSERT INTO daily_champions 
            (comment_id, subreddit, score, body, author, permalink, submission_title, created_utc, recorded_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        
    except Exception as e:
        logger.error(f"Failed to store record: {str(e)}")
        raise
    finally:
        conn.close()

def update_all_time_champion(comment_data):
    """Update all-time champion if this comment has more downvotes"""
    logger.info(f"Checking all-time champion against score: {comment_data['score']}")
    
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()

    try:
        # Convert datetime objects to strings
        created_utc = comment_data['created_utc'].isoformat() if isinstance(comment_data['created_utc'], datetime) else comment_data['created_utc']
        recorded_date = datetime.now().date().isoformat()

        # Get current champion's score
        c.execute('SELECT score FROM all_time_champion LIMIT 1')
        current_champion = c.fetchone()

        if not current_champion or comment_data['score'] < current_champion[0]:
            logger.info(f"New all-time champion found! Score: {comment_data['score']}")

            # Replace the current all-time champion
            c.execute('DELETE FROM all_time_champion')  # Clear old champion
            c.execute('''
                INSERT INTO all_time_champion 
                (comment_id, subreddit, score, body, author, permalink, 
                 submission_title, created_utc, recorded_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        logger.error(f"Error updating all-time champion: {str(e)}")
        raise
    finally:
        conn.close()

def store_subreddit_historical_data(subreddit, data):
    """Store daily collection data in historical record"""
    logger.info(f"Storing historical data for r/{subreddit}")
    
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    
    collection_date = datetime.now().date().isoformat()
    
    try:
        c.execute('''
            INSERT OR REPLACE INTO subreddit_historical_data
            (subreddit, collection_date, downvoted_comments, total_downvotes, total_comments)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            subreddit,
            collection_date,
            data['downvoted_comments'],
            data['total_downvotes'],
            data['total_comments']
        ))
        
        conn.commit()
        logger.info(f"Successfully stored historical data for r/{subreddit}")
        
    except Exception as e:
        logger.error(f"Failed to store historical data for r/{subreddit}: {str(e)}")
        raise
    finally:
        conn.close()

def get_all_time_champion():
    """Fetch the all-time champion from the database"""
    logger.info("Fetching all-time champion")
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    
    try:
        c.execute('SELECT * FROM all_time_champion LIMIT 1')
        result = c.fetchone()

        if result:
            logger.info(f"All-time champion found with score: {result[3]}")
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
        logger.info("No all-time champion found")
        return None
    except Exception as e:
        logger.error(f"Error fetching all-time champion: {str(e)}")
        raise
    finally:
        conn.close()

def store_subreddit_totals(subreddit, total_downvotes, total_comments):
    """Store daily totals for a subreddit in the database"""
    logger.info(f"Storing daily totals for r/{subreddit}")
    
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    
    recorded_date = datetime.now().date().isoformat()
    
    try:
        # Store in historical data
        data = {
            'downvoted_comments': total_comments,  # This is count of downvoted comments
            'total_downvotes': total_downvotes,
            'total_comments': total_comments
        }
        store_subreddit_historical_data(subreddit, data)
        
        # Also update the existing all_time_subreddit_totals for backward compatibility
        c.execute('''
            INSERT OR REPLACE INTO all_time_subreddit_totals 
            (subreddit, total_downvotes, total_comments, last_updated)
            VALUES (?, ?, ?, ?)
        ''', (
            subreddit,
            total_downvotes,
            total_comments,
            recorded_date
        ))
        
        conn.commit()
        logger.info(f"Successfully stored totals for r/{subreddit}")
        
    except Exception as e:
        logger.error(f"Failed to store totals: {str(e)}")
        raise
    finally:
        conn.close()

def get_subreddit_historical_totals():
    """Get historical totals for all subreddits"""
    logger.info("Fetching subreddit historical totals")
    
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    try:
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
    except Exception as e:
        logger.error(f"Error fetching historical totals: {str(e)}")
        raise
    finally:
        conn.close()

def get_stored_daily_champion(subreddit):
    """Get today's champion from database for given subreddit"""
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        SELECT * FROM daily_champions 
        WHERE subreddit = ?
        ORDER BY id DESC LIMIT 1
    ''', (subreddit,))
    
    result = c.fetchone()
    conn.close()
    
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
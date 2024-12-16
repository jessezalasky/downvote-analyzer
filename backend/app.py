from flask import Flask, jsonify, make_response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from logging.handlers import RotatingFileHandler
import sqlite3
from functools import wraps
from datetime import datetime, timedelta
from database import (
    get_all_time_champion,
    init_db,
    get_subreddit_historical_totals,
    get_stored_daily_champion
)
from config import Config

# Configuration
config = Config()

# Configure logging
handler = RotatingFileHandler(
    filename=config.LOG_FILE,
    maxBytes=config.LOG_MAX_BYTES,
    backupCount=config.LOG_BACKUP_COUNT
)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger = logging.getLogger('app')
logger.setLevel(getattr(logging, config.LOG_LEVEL))
logger.addHandler(handler)

# Initialize Flask app
app = Flask(__name__)

CORS(app, resources={
    r"/api/*": {
        "origins": config.ALLOWED_ORIGINS,
        "methods": ["GET", "OPTIONS"],
        "allow_headers": ["Content-Type", "Cache-Control", "Pragma"],  # Added Cache-Control and Pragma
        "expose_headers": ["Cache-Control"],
        "supports_credentials": True
    }
})

# Configure rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[
        f"{config.RATE_LIMIT_PER_MINUTE} per minute",
        f"{config.RATE_LIMIT_PER_HOUR} per hour"
    ]
)

# Simple in-memory cache
cache_store = {}

def cache_with_timeout(timeout=86400):  # 24 hours default
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            cache_key = f'{f.__name__}:{str(args)}:{str(kwargs)}'
            
            # Check if we have a valid cached response
            if cache_key in cache_store:
                cached_data, timestamp = cache_store[cache_key]
                if datetime.now() - timestamp < timedelta(seconds=timeout):
                    logger.info(f"Cache hit for {cache_key}")
                    return cached_data
            
            # If no cache hit, generate new response
            logger.info(f"Cache miss for {cache_key}")
            response = f(*args, **kwargs)
            
            # Store in cache
            cache_store[cache_key] = (response, datetime.now())
            
            return response
        return wrapper
    return decorator

def add_cache_headers(response):
    """Add cache control headers to response"""
    response.headers['Cache-Control'] = 'public, max-age=86400'  # 24 hours
    response.headers['Varies'] = 'Accept-Encoding'
    return response

# Initialize database
logger.info("Initializing database...")
init_db()
logger.info(f"Database initialized")

@app.route('/api/all-time-champion')
@cache_with_timeout(86400)
def get_champion():
    try:
        logger.info("Fetching all-time champion")
        champion = get_all_time_champion()
        response = make_response(jsonify({'champion': champion}))
        return add_cache_headers(response)
    except Exception as e:
        logger.error(f"Error fetching all-time champion: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/comments/<subreddit>')
@cache_with_timeout(86400)
def get_comments(subreddit):
    try:
        logger.info(f"Fetching comments for {subreddit}")
        stored_champion = get_stored_daily_champion(subreddit)
        logger.info(f"Stored champion data: {stored_champion}")
        
        response = make_response(jsonify({'comments': [stored_champion] if stored_champion else []}))
        return add_cache_headers(response)
    except Exception as e:
        logger.error(f"Error in get_comments for r/{subreddit}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/subreddit-totals')
@cache_with_timeout(86400)
def subreddit_totals():
    try:
        logger.info("Received request for subreddit totals")
        totals = get_subreddit_totals()
        logger.info(f"Subreddit totals dates: {[t.get('collection_date') for t in totals if isinstance(t, dict)]}")  # Added logging
        response = make_response(jsonify({'totals': totals}))
        return add_cache_headers(response)
    except Exception as e:
        logger.error(f"Error processing subreddit totals request: {str(e)}", exc_info=True)  # Added exc_info=True
        return jsonify({'error': str(e)}), 500

@app.route('/api/weekly-trends')
@cache_with_timeout(86400)
def weekly_trends():
    try:
        logger.info("Received request for weekly trends")
        trends = get_weekly_trends()
        response = make_response(jsonify({'trends': trends}))
        return add_cache_headers(response)
    except Exception as e:
        logger.error(f"Error processing weekly trends request: {str(e)}")
        return jsonify({'error': str(e)}), 500

def get_weekly_trends():
    """Get 7 days of downvote data for all subreddits"""
    logger.info("Fetching weekly trends")
    
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    try:
        c.execute('''
            SELECT 
                subreddit,
                collection_date,
                total_downvotes,
                total_comments
            FROM subreddit_historical_data
            WHERE collection_date >= date('now', '-7 days')
            ORDER BY collection_date DESC, total_downvotes ASC
        ''')

        results = c.fetchall()
        trends = {}
        
        for row in results:
            subreddit = row['subreddit']
            if subreddit not in trends:
                trends[subreddit] = []
            trends[subreddit].append({
                'date': row['collection_date'],
                'downvotes': row['total_downvotes'],
                'comments': row['total_comments']
            })

        return trends
    except Exception as e:
        logger.error(f"Error fetching weekly trends: {str(e)}")
        raise
    finally:
        conn.close()

def get_subreddit_totals():
    """Get latest totals for all subreddits"""
    logger.info("Fetching subreddit totals")

    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    try:
        c.execute('''
            SELECT t1.*
            FROM subreddit_historical_data t1
            INNER JOIN (
                SELECT subreddit, MAX(collection_date) as max_date
                FROM subreddit_historical_data
                GROUP BY subreddit
            ) t2
            ON t1.subreddit = t2.subreddit 
            AND t1.collection_date = t2.max_date
            ORDER BY t1.total_downvotes ASC
        ''')

        results = c.fetchall()
        totals = []
        
        for row in results:
            totals.append({
                'subreddit': row['subreddit'],
                'total_downvotes': row['total_downvotes'],
                'total_comments': row['total_comments'],
                'recorded_date': row['collection_date']
            })

        logger.info(f"Found totals for {len(totals)} subreddits")
        return totals
    except Exception as e:
        logger.error(f"Error fetching subreddit totals: {str(e)}")
        raise
    finally:
        conn.close()

@app.route('/api/comments/batch')
@cache_with_timeout(86400)
def get_comments_batch():
    try:
        logger.info("Fetching batch comments for all subreddits")
        results = {}
        
        # Get all stored champions for all subreddits
        conn = sqlite3.connect(config.DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute('''
            SELECT DISTINCT subreddit, 
                   comment_id,
                   score,
                   body,
                   author,
                   permalink,
                   submission_title,
                   created_utc,
                   recorded_date
            FROM daily_champions
            WHERE (subreddit, recorded_date) IN (
                SELECT subreddit, MAX(recorded_date)
                FROM daily_champions
                GROUP BY subreddit
            )
        ''')
        
        rows = c.fetchall()
        conn.close()
        
        results = {row['subreddit']: {
            'comment_id': row['comment_id'],
            'subreddit': row['subreddit'],
            'score': row['score'],
            'body': row['body'],
            'author': row['author'],
            'permalink': row['permalink'],
            'submission_title': row['submission_title'],
            'created_utc': row['created_utc'],
            'recorded_date': row['recorded_date']
        } for row in rows}
        
        logger.info(f"Batch comments dates: {set(r['recorded_date'] for r in results.values())}") 
        response = make_response(jsonify({'comments': results}))
        return add_cache_headers(response)
    except Exception as e:
        logger.error(f"Error in batch comments: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )
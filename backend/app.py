from flask import Flask, jsonify, make_response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
from functools import wraps
from database import (
    get_all_time_champion,
    init_db,
    get_subreddit_historical_totals,
    get_stored_daily_champion,
    test_database_connection,
    db_manager
)
from config import config


# Configure logging
logger = logging.getLogger('app')
logger.setLevel(logging.INFO)

# Create handler
handler = RotatingFileHandler(
    filename=config.LOG_FILE,
    maxBytes=config.LOG_MAX_BYTES,
    backupCount=config.LOG_BACKUP_COUNT
)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# After your imports
logger.info("Starting Reddit Downvote Analyzer API")

# Initialize database
logger.info("Initializing database...")
try:
    init_db()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Database initialization failed: {str(e)}")
    raise

# Test database connection
logger.info("Testing database connection...")
if not test_database_connection():
    logger.error("Failed to establish database connection at startup")
    raise RuntimeError("Could not connect to database")
logger.info("Database connection verified successfully")

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

# Configure CORS
CORS(app, resources={r"/api/*": {"origins": ["https://www.downvotedb.com", "https://downvotedb.com"]}})

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
logger.info("Database initialized")

@app.route('/api/all-time-champion')
@cache_with_timeout(600)
def get_champion():
    try:
        logger.info("Fetching all-time champion")
        champion = get_all_time_champion()
        response = make_response(jsonify({'champion': champion}))
        return add_cache_headers(response)
    except Exception as e:
        logger.error(f"Error fetching all-time champion: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/comments/<subreddit>')
@cache_with_timeout(600)
def get_comments(subreddit):
    try:
        logger.info(f"Fetching comments for {subreddit}")
        stored_champion = get_stored_daily_champion(subreddit)
        
        response = make_response(jsonify({'comments': [stored_champion] if stored_champion else []}))
        return add_cache_headers(response)
    except Exception as e:
        logger.error(f"Error in get_comments for r/{subreddit}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/all-time-subreddit-totals')
@cache_with_timeout(600)
def all_time_subreddit_totals():
    try:
        logger.info("Fetching all-time subreddit totals")
        totals = get_subreddit_historical_totals()
        response = make_response(jsonify({'totals': totals}))
        return add_cache_headers(response)
    except Exception as e:
        logger.error(f"Error processing all-time totals request: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/subreddit-totals')
@cache_with_timeout(600)
def subreddit_totals():
    try:
        logger.info("Fetching subreddit totals")
        conn = db_manager.get_connection()
        totals = []
        
        try:
            with conn.cursor() as cur:
                cur.execute('''
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
                
                results = cur.fetchall()
                totals = [{
                    'subreddit': row[1],
                    'total_downvotes': row[4],
                    'total_comments': row[5],
                    'recorded_date': row[2].isoformat()
                } for row in results]
                
        finally:
            db_manager.return_connection(conn)
        
        response = make_response(jsonify({'totals': totals}))
        return add_cache_headers(response)
    except Exception as e:
        logger.error(f"Error processing subreddit totals request: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/comments/batch')
@cache_with_timeout(600)
def get_comments_batch():
    try:
        logger.info("Fetching batch comments for all subreddits")
        conn = db_manager.get_connection()
        
        try:
            with conn.cursor() as cur:
                # First try to get today's comments
                cur.execute('''
                    WITH latest_date AS (
                        SELECT MAX(recorded_date) as max_date
                        FROM daily_champions
                    )
                    SELECT 
                        dc.subreddit,
                        dc.comment_id,
                        dc.score,
                        dc.body,
                        dc.author,
                        dc.permalink,
                        dc.submission_title,
                        dc.created_utc,
                        dc.recorded_date
                    FROM daily_champions dc
                    WHERE dc.recorded_date = (SELECT max_date FROM latest_date)
                ''')
                
                rows = cur.fetchall()
                
                results = {row[0]: {
                    'comment_id': row[1],
                    'subreddit': row[0],
                    'score': row[2],
                    'body': row[3],
                    'author': row[4],
                    'permalink': row[5],
                    'submission_title': row[6],
                    'created_utc': row[7].isoformat() if row[7] else None,
                    'recorded_date': row[8].isoformat() if row[8] else None
                } for row in rows}
                
        finally:
            db_manager.return_connection(conn)
        
        response = make_response(jsonify({'comments': results}))
        return add_cache_headers(response)
        
    except Exception as e:
        logger.error(f"Error in batch comments: {str(e)}")
        logger.exception("Full traceback:")
        return jsonify({'error': str(e)}), 500

@app.route('/api/weekly-trends')
@cache_with_timeout(600)
def weekly_trends():
    try:
        logger.info("Fetching weekly trends")
        conn = db_manager.get_connection()
        trends = {}
        
        try:
            with conn.cursor() as cur:
                cur.execute('''
                    SELECT 
                        subreddit,
                        collection_date,
                        total_downvotes,
                        total_comments
                    FROM subreddit_historical_data
                    WHERE collection_date >= current_date - interval '7 days'
                    ORDER BY collection_date DESC, total_downvotes ASC
                ''')
                
                results = cur.fetchall()
                
                for row in results:
                    subreddit = row[0]
                    if subreddit not in trends:
                        trends[subreddit] = []
                    trends[subreddit].append({
                        'date': row[1].isoformat(),
                        'downvotes': row[2],
                        'comments': row[3]
                    })
                
        finally:
            db_manager.return_connection(conn)
        
        response = make_response(jsonify({'trends': trends}))
        return add_cache_headers(response)
    except Exception as e:
        logger.error(f"Error processing weekly trends request: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/health')
def health_check():
    """API health check endpoint"""
    try:
        # Test database connection
        if test_database_connection():
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'status': 'unhealthy',
                'database': 'disconnected',
                'timestamp': datetime.now().isoformat()
            }), 500
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    logger.info(f"Starting Flask server on {config.HOST}:{config.PORT}")
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )

@app.teardown_appcontext
def cleanup(exception=None):
    """Cleanup function that runs after each request"""
    pass  # Connection cleanup is handled by the connection pool

# Test database connection at startup
if not test_database_connection():
    logger.error("Failed to establish database connection at startup")
    raise RuntimeError("Could not connect to database")

logger.info("Database connection verified")

if __name__ == '__main__':
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )
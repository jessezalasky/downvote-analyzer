import os
import schedule
import time
import logging
import json
import pytz
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Database and environment configuration
PG_USER = os.getenv('PGUSER')
PG_HOST = os.getenv('PGHOST')
PG_PASSWORD = os.getenv('PGPASSWORD')
PG_DATABASE = os.getenv('PGDATABASE')
PG_PORT = os.getenv('PGPORT', 5432)

# Local imports
from daily_downvotes import get_daily_worst_comment
from database import init_db
from category_map import get_all_subreddits
from config import config

# Configure logger
logger = logging.getLogger('scheduler')
handler = RotatingFileHandler(
    filename='scheduler.log',
    maxBytes=1024 * 1024,  # 1MB per file
    backupCount=7  # Keep 7 backup files
)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
def process_subreddit(subreddit):
    """Process a single subreddit with error handling and retries"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logger.info(f"Processing subreddit: {subreddit}")
            result = get_daily_worst_comment(subreddit)
            logger.info(f"Successfully processed {subreddit}")
            return True
        except Exception as e:
            retry_count += 1
            wait_time = 2 ** retry_count  # Exponential backoff: 2, 4, 8 seconds
            if retry_count < max_retries:
                logger.warning(f"Attempt {retry_count} failed for {subreddit}. Retrying in {wait_time} seconds. Error: {str(e)}")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to process {subreddit} after {max_retries} attempts. Error: {str(e)}")
                return False

def run_collection():
    """Main collection function that runs daily"""
    start_time = datetime.now()
    logger.info("Starting daily collection run")
    
    try:
        # Initialize database if needed
        init_db()
        
        # Get list of subreddits
        subreddits = get_all_subreddits()
        
        # Track results
        results = {
            'successful': [],
            'failed': [],
            'start_time': start_time.isoformat(),
            'end_time': None,
            'total_subreddits': len(subreddits)
        }
        
        # Process each subreddit
        for i, subreddit in enumerate(subreddits, 1):
            logger.info(f"Processing {i}/{len(subreddits)}: r/{subreddit}")
            success = process_subreddit(subreddit)
            if success:
                results['successful'].append(subreddit)
                logger.info(f"Successfully processed r/{subreddit}")
            else:
                results['failed'].append(subreddit)
                logger.error(f"Failed to process r/{subreddit}")
        
        # Record completion
        end_time = datetime.now()
        results['end_time'] = end_time.isoformat()
        results['duration'] = str(end_time - start_time)
        
        # Log summary
        logger.info(f"Collection run complete. Duration: {end_time - start_time}")
        logger.info(f"Successful: {len(results['successful'])}/{len(subreddits)}")
        if results['failed']:
            logger.warning(f"Failed subreddits: {', '.join(results['failed'])}")
        
        # Save results to JSON file with UTC timestamp
        timestamp = datetime.now(pytz.UTC).strftime("%Y%m%d_%H%M%S")
        result_file = f'collection_results_{timestamp}.json'
        
        try:
            with open(result_file, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results saved to {result_file}")
        except Exception as e:
            logger.error(f"Failed to save results file: {str(e)}")
            
    except Exception as e:
        logger.error(f"Collection run failed: {str(e)}")
        raise

def main():
    # Configure logging immediately
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        force=True
    )
    
    logger.info("Starting scheduler")
    
    try:
        # Schedule daily run for specified time
        pst = pytz.timezone('America/Los_Angeles')
        schedule_time = "21:00"  # You can adjust this time as needed
        
        # Schedule the job
        schedule.every().day.at(schedule_time).do(run_collection)
        logger.info(f"Scheduled daily collection for {schedule_time} PST")
        
        logger.info("Entering main scheduler loop")
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler crashed: {str(e)}")
        raise
    finally:
        # Ensure connections are cleaned up
        try:
            from database import close_db_pool  # Import here to avoid circular imports
            close_db_pool()
            logger.info("Cleaned up database connections")
        except Exception as e:
            logger.error(f"Error during final cleanup: {str(e)}")

if __name__ == "__main__":
    print("Scheduler script starting...")  # Immediate feedback for debugging
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error in scheduler: {str(e)}")
        raise
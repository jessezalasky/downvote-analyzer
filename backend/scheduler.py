import schedule
import time
import logging
from datetime import datetime
import pytz
from logging.handlers import RotatingFileHandler
import json
from daily_downvotes import get_daily_worst_comment
from database import init_db, db_manager
from category_map import get_all_subreddits
from config import config

# Configure logging
handler = RotatingFileHandler(
    filename=config.LOG_FILE,
    maxBytes=config.LOG_MAX_BYTES,
    backupCount=config.LOG_BACKUP_COUNT
)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger = logging.getLogger('scheduler')
logger.setLevel(getattr(logging, config.LOG_LEVEL))
logger.addHandler(handler)

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
    finally:
        try:
            # Cleanup any remaining database connections
            db_manager.pool.closeall()
            logger.info("Closed all database connections")
        except Exception as e:
            logger.error(f"Error during connection cleanup: {str(e)}")

def main():
    logger.info("Starting scheduler")
    
    # Schedule daily run for 9:00 PM PST
    pst = pytz.timezone('America/Los_Angeles')
    schedule_time = "21:00"
    
    # Schedule the job
    schedule.every().day.at(schedule_time).do(run_collection)
    logger.info(f"Scheduled daily collection for {schedule_time} PST")
    
    # Run immediately if specified
    if config.DEBUG:
        logger.info("Debug mode: Running initial collection immediately")
        run_collection()
    
    try:
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
            db_manager.pool.closeall()
            logger.info("Cleaned up database connections")
        except Exception as e:
            logger.error(f"Error during final cleanup: {str(e)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error in scheduler: {str(e)}")
        raise
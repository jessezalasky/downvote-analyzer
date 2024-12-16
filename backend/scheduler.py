import schedule
import time
import logging
from datetime import datetime
import pytz
from daily_downvotes import get_daily_worst_comment
from database import init_db
from category_map import get_all_subreddits
import json

# Keep your existing logging setup
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    filename='downvoter.log',
    maxBytes=1024 * 1024,  # 1MB per file
    backupCount=7  # Keep 7 backup files
)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger = logging.getLogger('scheduler')
logger.setLevel(logging.INFO)
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
            if retry_count < max_retries:
                wait_time = 2 ** retry_count  # Exponential backoff: 2, 4, 8 seconds
                logging.warning(f"Attempt {retry_count} failed for {subreddit}. Retrying in {wait_time} seconds. Error: {str(e)}")
                time.sleep(wait_time)
            else:
                logging.error(f"Failed to process {subreddit} after {max_retries} attempts. Error: {str(e)}")
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
            'end_time': None
        }
        
        # Process each subreddit
        for subreddit in subreddits:
            success = process_subreddit(subreddit)
            if success:
                results['successful'].append(subreddit)
            else:
                results['failed'].append(subreddit)
        
        # Record completion
        end_time = datetime.now()
        results['end_time'] = end_time.isoformat()
        
        # Log summary
        logger.info(f"Collection run complete. Duration: {end_time - start_time}")
        logger.info(f"Successful: {len(results['successful'])}/{len(subreddits)}")
        if results['failed']:
            logging.warning(f"Failed subreddits: {', '.join(results['failed'])}")
        
        # Save results to JSON file with UTC timestamp
        timestamp = datetime.now(pytz.UTC).strftime("%Y%m%d_%H%M%S")
        with open(f'collection_results_{timestamp}.json', 'w') as f:
            json.dump(results, f, indent=2)
            
    except Exception as e:
        logger.error(f"Collection run failed: {str(e)}")
        raise

def main():
    print("Entering main function")  # Add this
    logging.info("Setting up scheduler")  # Add this
    # Schedule daily run for 9:00 PM PST
    pst = pytz.timezone('America/Los_Angeles')
    schedule.every().day.at("21:50").do(run_collection)  # 9 PM PST

    logging.info("Scheduler started. Will run daily at 21:00 PST")  # Add this
    print("Scheduler is running...")  # Add this
    
    logger.info("Scheduler started. Will run daily at 21:00 PST")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    try:
        print("Scheduler starting up...")  # Add this
        logging.info("Scheduler service initializing")  # Add this
        main()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logging.error(f"Scheduler crashed: {str(e)}", exc_info=True)
        raise
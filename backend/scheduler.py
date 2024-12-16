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
    print("Entering main function")
    logging.info("Setting up scheduler")
    
    # Initialize database if not exists
    init_db()
    
    # Schedule daily run for 9:50 PM PST
    pst = pytz.timezone('America/Los_Angeles')
    schedule.every().day.at("22:08").do(run_collection)  # 9:50 PM PST
    
    logging.info("Scheduler started. Will run daily at 22:08 PST")
    print("Scheduler is running...")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    print("Starting scheduler script")  # Add this
    try:
        print("About to initialize database")  # Add this
        init_db()  # Try calling it here instead of in main()
        print("Database initialized")  # Add this
        main()
    except Exception as e:
        print(f"Error: {str(e)}")  # Add this
        raise
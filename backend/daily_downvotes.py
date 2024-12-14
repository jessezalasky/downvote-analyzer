import praw
import pandas as pd
from datetime import datetime, timedelta
import logging
from database import store_daily_champion, update_all_time_champion, init_db
from config import config

def initialize_reddit():
    """Initialize Reddit API connection"""
    return praw.Reddit(
        client_id=config.REDDIT_CLIENT_ID,
        client_secret=config.REDDIT_CLIENT_SECRET,
        user_agent=config.REDDIT_USER_AGENT
    )

def get_daily_worst_comment(subreddit_name):
    reddit = initialize_reddit()
    subreddit = reddit.subreddit(subreddit_name)
    comments_data = []
    posts_checked = 0
    posts_in_timeframe = 0
    current_worst_score = 0
    
    time_2h_ago = datetime.utcnow() - timedelta(hours=config.COLLECTION_DELAY_HOURS)
    time_24h_ago = datetime.utcnow() - timedelta(hours=config.COLLECTION_WINDOW_HOURS)
    
    logging.info(f"\nAnalyzing r/{subreddit_name} for posts between {config.COLLECTION_DELAY_HOURS} and {config.COLLECTION_WINDOW_HOURS} hours old")
    logging.info(f"Collection window: {time_24h_ago} to {time_2h_ago}")
    
    for submission in subreddit.new(limit=None):
        posts_checked += 1
        post_time = datetime.fromtimestamp(submission.created_utc)
        
        # Skip posts newer than 2 hours
        if post_time > time_2h_ago:
            continue
            
        # Break if we've reached posts older than 24 hours
        if post_time < time_24h_ago:
            logging.info(f"\nReached posts older than 24 hours after checking {posts_checked} posts")
            break
            
        posts_in_timeframe += 1
        logging.info(f"\nChecking post #{posts_in_timeframe}: {submission.title[:50]}...")
        
        submission.comments.replace_more(limit=0)
        for comment in submission.comments.list():
            if not comment.stickied and hasattr(comment, 'score'):
                if comment.score < -1 and comment.body not in ["[deleted]", "[removed]"]:
                    if comment.score < current_worst_score:
                        current_worst_score = comment.score
                        logging.info(f"New worst comment found! Score: {comment.score}")
                    
                    comments_data.append({
                        'comment_id': comment.id,
                        'score': comment.score,
                        'created_utc': datetime.fromtimestamp(comment.created_utc),
                        'body': comment.body[:500],
                        'author': str(comment.author),
                        'permalink': f'https://reddit.com{comment.permalink}',
                        'submission_title': submission.title,
                        'subreddit': subreddit_name
                    })

    df = pd.DataFrame(comments_data)
    if not df.empty:
        df = df.drop_duplicates(subset='comment_id')
        
        # Calculate and store total downvotes
        try:
            calculate_subreddit_totals(df)
        except Exception as e:
            logging.info(f"Error calculating subreddit totals: {str(e)}")
        
        # Continue with worst comment processing
        df = df.sort_values('score', ascending=True)
        worst_comment = df.iloc[0]  
        df = df.sort_values('score', ascending=True)
        worst_comment = df.iloc[0] 
        
        # Convert to dict for database storage
        comment_data = worst_comment.to_dict()
        logging.info(f"Found worst comment with score: {comment_data['score']}")
        
# Store as daily champion and update all-time
        try:
            logging.info(f"\nAttempting to store comment for r/{comment_data['subreddit']}")
            logging.info(f"Comment data: Score {comment_data['score']}, ID: {comment_data['comment_id']}")
            store_daily_champion(comment_data)
            update_all_time_champion(comment_data)  # Add this line
            logging.info("Storage successful")
        except Exception as e:
            logging.info(f"Error storing comment: {str(e)}")
            raise
        
        logging.info(f"\nAnalysis Complete:")
        logging.info(f"Total posts checked: {posts_checked}")
        logging.info(f"Posts in time window: {posts_in_timeframe}")
        logging.info(f"Total downvoted comments found: {len(df)}")
        
        return pd.DataFrame([worst_comment])
    
    logging.info("\nNo qualifying downvoted comments found")
    return pd.DataFrame()

def calculate_subreddit_totals(df):
    """Calculate and store total downvotes and comment counts per subreddit, preventing duplicates."""
    if df.empty:
        logging.info("No downvoted comments to process for totals")
        return

    subreddit_totals = defaultdict(lambda: {'total_downvotes': 0, 'total_comments': 0})  # Use defaultdict

    for _, row in df.iterrows():  # Iterate through the DataFrame once
        subreddit = row['subreddit']
        subreddit_totals[subreddit]['total_downvotes'] += row['score']
        subreddit_totals[subreddit]['total_comments'] += 1

    logging.info(f"\nCalculating totals for {len(subreddit_totals)} subreddits")

    for subreddit, totals in subreddit_totals.items(): # Iterate through accumulated values and store/update
        try:
            store_subreddit_totals(subreddit, totals['total_downvotes'], totals['total_comments'])
            update_all_time_subreddit_totals(subreddit, totals['total_downvotes'], totals['total_comments'])
        except Exception as e:
            logging.info(f"Error storing totals for r/{subreddit}: {str(e)}")
            continue  # Or handle the error as needed
        
    # Group by subreddit and calculate totals
    subreddit_totals = df.groupby('subreddit').agg({
        'score': ['sum', 'count']
    }).reset_index()
    
    # Flatten column names
    subreddit_totals.columns = ['subreddit', 'total_downvotes', 'total_comments']
    
    logging.info(f"\nCalculating totals for {len(subreddit_totals)} subreddits")
    
    # Store totals for each subreddit
    for _, row in subreddit_totals.iterrows():
        try:
            # Store daily totals
            store_subreddit_totals(row['subreddit'], row['total_downvotes'], row['total_comments'])
            
            # Update all-time totals
            update_all_time_subreddit_totals(row['subreddit'], row['total_downvotes'], row['total_comments'])
        except Exception as e:
            logging.info(f"Error storing totals for r/{row['subreddit']}: {str(e)}")
            continue

def update_all_time_subreddit_totals(subreddit, daily_downvotes, daily_comments):
    """Update all-time totals for a subreddit by adding daily totals"""
    logging.info(f"Updating all-time totals for r/{subreddit}")

    conn = sqlite3.connect(DB_PATH)  # Ensure DB_PATH is correct
    c = conn.cursor()

    try:
        # Get current totals if they exist
        c.execute('SELECT total_downvotes, total_comments FROM all_time_subreddit_totals WHERE subreddit = ?', (subreddit,))
        current = c.fetchone()
        logging.info(f"Current totals for r/{subreddit}: {current}")

        current_date = datetime.now().date().isoformat()

        if current:
            # Update existing totals
            logging.info(f"Updating existing totals for r/{subreddit}")
            c.execute('''
                UPDATE all_time_subreddit_totals
                SET total_downvotes = total_downvotes + ?,
                    total_comments = total_comments + ?,
                    last_updated = ?
                WHERE subreddit = ?
            ''', (daily_downvotes, daily_comments, current_date, subreddit))
            logging.info("Update query executed.")
        else:
            # Insert new record
            logging.info(f"Inserting new record for r/{subreddit}")
            c.execute('''
                INSERT INTO all_time_subreddit_totals
                (subreddit, total_downvotes, total_comments, last_updated)
                VALUES (?, ?, ?, ?)
            ''', (subreddit, daily_downvotes, daily_comments, current_date))
            logging.info("Insert query executed.")

        conn.commit()
        logging.info(f"Successfully updated all-time totals for r/{subreddit}")

    except Exception as e:
        logging.error(f"Error updating all-time totals for r/{subreddit}: {str(e)}")
        # Handle the exception here (e.g., log and continue) instead of raising it
    finally:
        conn.close()

def main():
    # Initialize database if not exists
    init_db()

    # Get all subreddits from category map
    from category_map import get_all_subreddits
    subreddits = get_all_subreddits()
    
    logging.info(f"Processing {len(subreddits)} subreddits...")
    
    for subreddit in subreddits:
        try:
            df = get_daily_worst_comment(subreddit)
            if not df.empty:
                comment = df.iloc[0]
                logging.info(f"\nProcessed r/{subreddit}")
                logging.info(f"Worst Comment Score: {comment['score']}")
        except Exception as e:
            logging.error(f"Error processing r/{subreddit}: {str(e)}")
            continue

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        filename=config.LOG_FILE,
        level=getattr(logging, config.LOG_LEVEL),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    main()
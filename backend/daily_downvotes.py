from collections import defaultdict
import praw
import pandas as pd
from datetime import datetime, timedelta
import logging
from database import (
    store_daily_champion,
    update_all_time_champion,
    init_db,
    db_manager,
    store_subreddit_totals
)
from config import config

logger = logging.getLogger(__name__)

def initialize_reddit():
    """Initialize Reddit API connection"""
    return praw.Reddit(
        client_id=config.REDDIT_CLIENT_ID,
        client_secret=config.REDDIT_CLIENT_SECRET,
        user_agent=config.REDDIT_USER_AGENT
    )

def get_daily_worst_comment(subreddit_name):
    """Collect and analyze daily worst comments for a subreddit"""
    reddit = initialize_reddit()
    subreddit = reddit.subreddit(subreddit_name)
    comments_data = []
    posts_checked = 0
    posts_in_timeframe = 0
    current_worst_score = 0
    
    time_2h_ago = datetime.utcnow() - timedelta(hours=config.COLLECTION_DELAY_HOURS)
    time_24h_ago = datetime.utcnow() - timedelta(hours=config.COLLECTION_WINDOW_HOURS)
    
    logger.info(f"\nAnalyzing r/{subreddit_name}")
    logger.info(f"Collection window: {time_24h_ago} to {time_2h_ago}")
    
    for submission in subreddit.new(limit=None):
        posts_checked += 1
        post_time = datetime.fromtimestamp(submission.created_utc)
        
        # Skip posts newer than delay window
        if post_time > time_2h_ago:
            continue
            
        # Break if we've reached posts older than collection window
        if post_time < time_24h_ago:
            logger.info(f"\nReached posts older than {config.COLLECTION_WINDOW_HOURS}h after checking {posts_checked} posts")
            break
            
        posts_in_timeframe += 1
        logger.info(f"\nChecking post #{posts_in_timeframe}: {submission.title[:50]}...")
        
        submission.comments.replace_more(limit=0)
        for comment in submission.comments.list():
            if not comment.stickied and hasattr(comment, 'score'):
                if comment.score < -1 and comment.body not in ["[deleted]", "[removed]"]:
                    if comment.score < current_worst_score:
                        current_worst_score = comment.score
                        logger.info(f"New worst comment found! Score: {comment.score}")
                    
                    comments_data.append({
                        'comment_id': comment.id,
                        'score': comment.score,
                        'created_utc': datetime.fromtimestamp(comment.created_utc),
                        'body': comment.body[:500],  # Limit comment length
                        'author': str(comment.author),
                        'permalink': f'https://reddit.com{comment.permalink}',
                        'submission_title': submission.title,
                        'subreddit': subreddit_name
                    })

    if comments_data:
        df = pd.DataFrame(comments_data)
        df = df.drop_duplicates(subset='comment_id')
        
        try:
            # Calculate and store subreddit totals
            total_downvotes = df['score'].sum()
            total_comments = len(df)
            store_subreddit_totals(subreddit_name, total_downvotes, total_comments)
            logger.info(f"Stored totals for r/{subreddit_name}: {total_downvotes} downvotes across {total_comments} comments")
        except Exception as e:
            logger.error(f"Error storing subreddit totals: {str(e)}")
        
        # Find and store worst comment
        df = df.sort_values('score', ascending=True)
        worst_comment = df.iloc[0].to_dict()
        
        try:
            logger.info(f"Storing worst comment for r/{subreddit_name} (score: {worst_comment['score']})")
            store_daily_champion(worst_comment)
            update_all_time_champion(worst_comment)
            logger.info("Successfully stored comment data")
        except Exception as e:
            logger.error(f"Error storing comment data: {str(e)}")
            raise
        
        logger.info(f"\nAnalysis Complete for r/{subreddit_name}:")
        logger.info(f"Total posts checked: {posts_checked}")
        logger.info(f"Posts in time window: {posts_in_timeframe}")
        logger.info(f"Total downvoted comments found: {len(df)}")
        
        return df.iloc[[0]]  # Return worst comment as DataFrame
    
    logger.info(f"\nNo qualifying downvoted comments found for r/{subreddit_name}")
    return pd.DataFrame()

def main():
    """Main function for testing"""
    init_db()
    from category_map import get_all_subreddits
    subreddits = get_all_subreddits()
    
    logger.info(f"Processing {len(subreddits)} subreddits...")
    
    for subreddit in subreddits:
        try:
            df = get_daily_worst_comment(subreddit)
            if not df.empty:
                comment = df.iloc[0]
                logger.info(f"\nProcessed r/{subreddit}")
                logger.info(f"Worst Comment Score: {comment['score']}")
        except Exception as e:
            logger.error(f"Error processing r/{subreddit}: {str(e)}")
            continue

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    main()
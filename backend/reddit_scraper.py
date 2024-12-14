import praw
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

def initialize_reddit():
    """Initialize Reddit API connection"""
    return praw.Reddit(
        client_id=os.getenv('REDDIT_CLIENT_ID'),
        client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
        user_agent=os.getenv('REDDIT_USER_AGENT', 'DownvoteAnalyzer/1.0')
    )

def get_extreme_comments(subreddit_name, submission_limit=50):
    """
    Efficiently retrieve heavily downvoted comments from a subreddit
    Using dynamic thresholds and early exit strategies
    """
    reddit = initialize_reddit()
    subreddit = reddit.subreddit(subreddit_name)
    comments_data = []
    
    # Initial threshold settings
    current_threshold = -500  # Start looking for very negative comments
    min_threshold = -50       # Don't bother with comments above this
    threshold_step = 100     # How much to reduce threshold when no results found
    posts_without_results = 0 # Counter for posts with no qualifying comments
    max_posts_without_results = 10  # Exit after this many posts with no results
    
    print(f"\nAnalyzing r/{subreddit_name}")
    print(f"Initial threshold: {current_threshold}")
    
    try:
        # Start with controversial posts as they're more likely to have downvoted comments
        submissions = list(subreddit.controversial(limit=submission_limit, time_filter='all'))
        
        for submission in tqdm(submissions, desc="Processing posts"):
            found_qualifying_comment = False
            submission.comments.replace_more(limit=0)  # Only get readily available comments
            
            # Check top-level comments first as they tend to be more visible and controversial
            for comment in submission.comments.list():
                if not comment.stickied and hasattr(comment, 'score'):
                    if comment.score <= current_threshold and comment.body not in ["[deleted]", "[removed]"]:
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
                        found_qualifying_comment = True
                        # Update threshold if we found a more downvoted comment
                        current_threshold = min(current_threshold, comment.score)
                        print(f"\nFound heavily downvoted comment (Score: {comment.score})")
                        print(f"New threshold: {current_threshold}")
            
            if not found_qualifying_comment:
                posts_without_results += 1
            else:
                posts_without_results = 0  # Reset counter when we find something
            
            # If we haven't found anything in several posts, lower our threshold
            if posts_without_results >= max_posts_without_results:
                old_threshold = current_threshold
                current_threshold += threshold_step  # Make threshold less negative
                if current_threshold > min_threshold:
                    print(f"\nReached minimum threshold without finding enough comments")
                    break
                print(f"\nLowering threshold from {old_threshold} to {current_threshold}")
                posts_without_results = 0  # Reset counter
                
    except Exception as e:
        print(f"Error processing subreddit: {e}")
    
    # Convert to DataFrame and sort
    df = pd.DataFrame(comments_data)
    if not df.empty:
        df = df.drop_duplicates(subset='comment_id')
        df = df.sort_values('score', ascending=True)  # Most downvoted first
    
    return df

def main():
    # List of subreddits to analyze
    subreddits = ['funny', 'gaming', 'movies']  # Add more as needed
    all_results = {}
    
    for subreddit in subreddits:
        df = get_extreme_comments(subreddit)
        if not df.empty:
            all_results[subreddit] = df
            
            print(f"\nResults for r/{subreddit}:")
            print(f"Total comments found: {len(df)}")
            print("\nMost downvoted comments:")
            for idx, row in df.head().iterrows():
                print(f"\nScore: {row['score']}")
                print(f"Link: {row['permalink']}")
                print("-" * 80)
    
    return all_results

if __name__ == "__main__":
    main()
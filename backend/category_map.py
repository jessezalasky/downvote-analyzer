# backend/category_map.py

CATEGORY_MAP = {
    'Entertainment': {
        'name': 'Entertainment',
        'subreddits': ['movies', 'television', 'gaming', 'music', 'funny', 'amitheasshole']
    },
    'Cities': {
        'name': 'Cities',
        'subreddits': ['sacramento', 'seattle', 'vancouver', 'denver', 'austin']
    },
    'News': {
        'name': 'News',
        'subreddits': ['worldnews', 'news', 'politics', 'science', 'technology']
    },
    'Hobbies': {
       'name': 'Hobbies',
        'subreddits': ['golf', 'thriftstorehauls', 'travel', 'aviation', 'coins']
    },
    'Sports': {
        'name': 'Sports',
        'subreddits': ['nba', 'nfl', 'nhl', 'baseball', 'formula1']
    }
}

def get_all_subreddits():
    """Return a flat list of all subreddits"""
    return [
        subreddit
        for category in CATEGORY_MAP.values()
        for subreddit in category['subreddits']
    ]

def get_category_for_subreddit(subreddit):
    """Return category name for a given subreddit"""
    for category, data in CATEGORY_MAP.items():
        if subreddit in data['subreddits']:
            return category
    return None
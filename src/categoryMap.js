// Categories and their associated subreddits
export const categoryMap = {
    Entertainment: {
      name: "Entertainment",
      subreddits: ["movies", "television", "music", "gaming", "funny", "amitheasshole"]
    },
    Cities: {
        name: "Cities",
        subreddits: ["sacramento", "seattle", "vancouver", "denver", "austin"]
    },
    News: {
      name: "News",
      subreddits: ["worldnews", "news", "politics", "science", "technology"]
    },
    Hobbies: {
        name: "Hobbies",
        subreddits: ["golf", "thriftstorehauls", "travel", "aviation", "coins"]
      },
    Sports: {
        name: "Sports",
        subreddits: ["nba", "nfl", "nhl", "baseball", "formula1"]
      }
  };
  
  // Helper to get all subreddits as a flat array
  export const getAllSubreddits = () => {
    return Object.values(categoryMap)
      .flatMap(category => category.subreddits);
  };
  
  // Helper to get category for a subreddit
  export const getCategoryForSubreddit = (subreddit) => {
    for (const [category, data] of Object.entries(categoryMap)) {
      if (data.subreddits.includes(subreddit)) {
        return category;
      }
    }
    return null;
  };
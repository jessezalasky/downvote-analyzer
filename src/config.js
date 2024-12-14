// Environment detection
const getEnvironment = () => {
  return process.env.REACT_APP_ENV || 'development';
};

// Config object
const config = {
  // Environment
  ENV: getEnvironment(),
  
  // API
  API_BASE_URL: process.env.REACT_APP_API_URL || 'https://downvotedb.com/api',
  
  // Feature flags
  ENABLE_CACHING: process.env.REACT_APP_ENABLE_CACHING === 'true',
  ENABLE_ANALYTICS: process.env.REACT_APP_ENABLE_ANALYTICS === 'true',
  
  // UI Settings
  MAX_COMMENTS_PER_PAGE: parseInt(process.env.REACT_APP_MAX_COMMENTS_PER_PAGE || '100'),
  REFRESH_INTERVAL: parseInt(process.env.REACT_APP_REFRESH_INTERVAL || '3600000'),

  // API Routes
  routes: {
    weeklyTrends: '/api/weekly-trends',
    allTimeChampion: '/api/all-time-champion',
    comments: (subreddit) => `/api/comments/${subreddit}`,
    subredditTotals: '/api/subreddit-totals'
  }
};

// Helper function to get full API URLs
export const getApiUrl = (route) => `${config.API_BASE_URL}${route}`;

// Freeze the config object to prevent modifications
export default Object.freeze(config);
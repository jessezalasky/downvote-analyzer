const API_BASE_URL = import.meta.env.VITE_API_URL;

class ApiService {
  constructor() {
    console.log('Environment variable value:', process.env.REACT_APP_API_URL);
    console.log('Final baseUrl value:', this.baseUrl);
    this.baseUrl = API_BASE_URL;
}

  async fetchWithCache(endpoint) {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        cache: 'default',
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'public, max-age=86400', // 24 hours
          'Pragma': 'cache'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Log cache status for debugging
      console.log(`Cache status for ${endpoint}:`, response.headers.get('Cache-Control'));

      return await response.json();
    } catch (error) {
      console.error(`Error fetching ${endpoint}:`, error);
      throw error;
    }
  }

  async getWeeklyTrends() {
    return this.fetchWithCache('/api/weekly-trends');
  }

  async getAllTimeChampion() {
    return this.fetchWithCache('/api/all-time-champion');
  }

  async getSubredditComments(subreddit) {
    return this.fetchWithCache(`/api/comments/${subreddit}`);
  }

  async getSubredditTotals() {
    return this.fetchWithCache('/api/subreddit-totals');
  }

  async getAllTimeSubredditTotals() {
    return this.fetchWithCache('/api/all-time-subreddit-totals');
  }

  async getCommentsBatch() {
    return this.fetchWithCache('/api/comments/batch');
  }
}

export default new ApiService();
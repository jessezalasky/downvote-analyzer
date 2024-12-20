import { useState, useEffect } from 'react';
import ApiService from './services/api';
import React from 'react';
import ReactGA from "react-ga4";
import AllTimeChampionCard from './components/AllTimeChampionCard';
import CategorySection from './components/CategorySection';
import TabNavigation from './components/TabNavigation';
import SubredditTotals from './components/SubredditTotals';
import AllTimeSubredditTotals from './components/AllTimeSubredditTotals';
import TrendAnalysis from './components/TrendAnalysis';
import { categoryMap } from './categoryMap';
import { colors, layout, typography } from './styles/design-tokens.js';

// Initialize GA4 only in production
if (import.meta.env.PROD) {
  ReactGA.initialize("G-FV4MZB3THV");
}

function App() {
  const [categorizedComments, setCategorizedComments] = useState({});
  const [champion, setChampion] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeView, setActiveView] = useState('categories');
  const [subredditTotals, setSubredditTotals] = useState([]);
  const [allTimeTotals, setAllTimeTotals] = useState([]);

  // Track initial page view
  useEffect(() => {
    if (import.meta.env.PROD) {
      ReactGA.send({ hitType: "pageview", page: window.location.pathname });
    }
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const championResponse = await ApiService.getAllTimeChampion();
        setChampion(championResponse.champion);

        const allTimeResponse = await ApiService.getAllTimeSubredditTotals();
        setAllTimeTotals(allTimeResponse.totals);

        const results = {};
        Object.keys(categoryMap).forEach(category => {
          results[category] = [];
        });

        const batchCommentsResponse = await ApiService.getCommentsBatch();

        Object.entries(batchCommentsResponse.comments).forEach(([subreddit, comment]) => {
          for (const [category, info] of Object.entries(categoryMap)) {
            if (info.subreddits.includes(subreddit)) {
              results[category].push(comment);
              break;
            }
          }
        });

        const subredditResponse = await ApiService.getSubredditTotals();
        const mostRecentDate = subredditResponse.totals[0]?.recorded_date;
        const filteredTotals = mostRecentDate ? 
          subredditResponse.totals.filter(total => total.recorded_date === mostRecentDate) : [];
        
        setSubredditTotals(filteredTotals);
        setAllTimeTotals(allTimeResponse.totals);

        Object.keys(results).forEach(category => {
          results[category].sort((a, b) => a.score - b.score);
        });

        setCategorizedComments(results);
      } catch (err) {
        setError('Failed to fetch data. Please try again later.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const getHeaderContent = () => {
    if (activeView === 'categories') {
      return {
        title: "Daily Downvotes by Category",
        description: "Check out the most downvoted comments in the last 24 hours in the most popular subreddits."
      };
    } else if (activeView === 'trends') {
      return {
        title: "Downvote Patterns by Subreddit",
        description: "Track how comment downvotes evolve over time for each subreddit in the past 7 days."
      };
    } else {
      return {
        title: "Daily Downvotes by Subreddit",
        description: "See which subreddits have accumulated the most comment downvotes in the past 24 hours."
      };
    }
  };

  if (loading) {
    return (
      <div className={`min-h-screen ${colors.bg.primary} p-4 flex items-center justify-center`}>
        <div className={`${typography.title} ${colors.text.primary}`}>Loading comments...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`min-h-screen ${colors.bg.primary} p-4 flex items-center justify-center`}>
        <div className={`${typography.title} ${colors.text.primary} text-red-500`}>{error}</div>
      </div>
    );
  }

  const headerContent = getHeaderContent();

  return (
    <div className={`min-h-screen ${colors.bg.primary} pt-8 pb-12`}>
      <div className={layout.container}>
        <h1 className={`${typography.title} ${colors.text.primary} text-center mb-8`}>
          Reddit Downvote Analyzer
        </h1>
  
        <div className="mb-8">
          <TabNavigation 
            activeView={activeView}
            onViewChange={setActiveView}
          />
        </div>
  
        {activeView === 'categories' && <AllTimeChampionCard champion={champion}/>}
        {activeView === 'subreddits' && <AllTimeSubredditTotals totals={allTimeTotals} />}
  
        <div className="mt-8 mb-8 text-center">
          <h2 className={`${typography.title} ${colors.text.primary} mb-2`}>
            {headerContent.title}
          </h2>
          <p className={`${typography.body} ${colors.text.secondary}`}>
            {headerContent.description}
          </p>
        </div>
  
        <div className="mt-6">
          {activeView === 'categories' ? (
            <CategorySection 
              categories={categoryMap}
              comments={categorizedComments}
            />
          ) : activeView === 'trends' ? (
            <TrendAnalysis />
          ) : (
            <SubredditTotals totals={subredditTotals} />
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
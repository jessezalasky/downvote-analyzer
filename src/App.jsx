import { useState, useEffect } from 'react';
import ApiService from './services/api';
import React from 'react';
import AllTimeChampionCard from './components/AllTimeChampionCard';
import CategorySection from './components/CategorySection';
import TabNavigation from './components/TabNavigation';
import SubredditTotals from './components/SubredditTotals';
import AllTimeSubredditTotals from './components/AllTimeSubredditTotals';
import TrendAnalysis from './components/TrendAnalysis';
import { categoryMap, getAllSubreddits } from './categoryMap';
import { colors, layout, typography } from './styles/design-tokens.js';


function App() {
  const [categorizedComments, setCategorizedComments] = useState({});
  const [champion, setChampion] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeView, setActiveView] = useState('categories');
  const [subredditTotals, setSubredditTotals] = useState([]);
  const [allTimeTotals, setAllTimeTotals] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        
        // Fetch champion
        const championResponse = await ApiService.getAllTimeChampion();
        setChampion(championResponse.champion);

        // Fetch all-time totals
        const allTimeResponse = await ApiService.getAllTimeSubredditTotals();
        setAllTimeTotals(allTimeResponse.totals);

// Initialize results object
const results = {};
Object.keys(categoryMap).forEach(category => {
  results[category] = [];
});

// Fetch all comments in one batch request
const batchCommentsResponse = await ApiService.getCommentsBatch();

// Categorize comments from batch response
Object.entries(batchCommentsResponse.comments).forEach(([subreddit, comment]) => {
  for (const [category, info] of Object.entries(categoryMap)) {
    if (info.subreddits.includes(subreddit)) {
      results[category].push(comment);
      break;
    }
  }
});

const subredditResponse = await ApiService.getSubredditTotals();
console.log("All time totals response:", allTimeResponse);

const mostRecentDate = subredditResponse.totals[0]?.recorded_date;
const filteredTotals = mostRecentDate ? 
    subredditResponse.totals.filter(total => total.recorded_date === mostRecentDate) : [];
setSubredditTotals(filteredTotals);
setAllTimeTotals(allTimeResponse.totals);  // Use the same response to set state

        

        // Sort comments within each category by score
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
        {/* Header always at top */}
        <h1 className={`${typography.title} ${colors.text.primary} text-center mb-8`}>
          Reddit Downvote Analyzer
        </h1>
  
        {/* Tab Navigation always second */}
        <div className="mb-8">
          <TabNavigation 
            activeView={activeView}
            onViewChange={setActiveView}
          />
        </div>
  
        {/* Optional top cards based on view */}
        {activeView === 'categories' && <AllTimeChampionCard champion={champion}/>}
        {activeView === 'subreddits' && <AllTimeSubredditTotals totals={allTimeTotals} />}
  
        {/* Dynamic Section Header */}
        <div className="mt-8 mb-8 text-center">
          <h2 className={`${typography.title} ${colors.text.primary} mb-2`}>
            {headerContent.title}
          </h2>
          <p className={`${typography.body} ${colors.text.secondary}`}>
            {headerContent.description}
          </p>
        </div>
  
        {/* Main Content Section */}
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

        
        
        {/* Tab Navigation First */}
        <div className="mt-12">
          <TabNavigation 
            activeView={activeView}
            onViewChange={setActiveView}
          />
        </div>

        {/* Dynamic Section Header Below Tabs */}
        <div className="mt-8 mb-8 text-center">
          <h2 className={`${typography.title} ${colors.text.primary} mb-2`}>
            {headerContent.title}
          </h2>
          <p className={`${typography.body} ${colors.text.secondary}`}>
            {headerContent.description}
          </p>
        </div>

        {/* Content Section */}
        <div className="mt-6">
          {activeView === 'categories' ? (
            <CategorySection 
              categories={categoryMap}
              comments={categorizedComments}
            />
          ) : (
            <SubredditTotals totals={subredditTotals} />
          )}
        </div>

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

  return (
    <div className={`min-h-screen ${colors.bg.primary} pt-8`}>
      <div className={layout.container}>
        <h1 className={`${typography.title} ${colors.text.primary} text-center mb-8`}>
          Reddit Downvote Analyzer
        </h1>
        
        <AllTimeChampionCard champion={champion} />
        
        {/* Section Header */}
        <div className="mb-8 mt-12 text-center">
          <div className="mb-4">
            <h2 className={`${typography.title} ${colors.text.primary} mb-2`}>
              Daily Downvoted by Category
            </h2>
          </div>
          <p className={`${typography.body} ${colors.text.secondary}`}>
            Check out the most downvoted comments in the last 24 hours in the most popular subreddits!
          </p>
        </div>

        {/* Add after the section header div */}
        <TabNavigation 
          activeView={activeView}
          onViewChange={setActiveView}
        />
      </div>
    </div>
  );
}

export default App;
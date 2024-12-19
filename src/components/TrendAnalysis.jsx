import React, { useState, useEffect } from 'react';
import { colors, layout, typography } from '../styles/design-tokens';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { categoryMap } from '../categoryMap';
import ApiService from '../services/api';

function TrendAnalysis() {
  const [trends, setTrends] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('Cities');
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchTrends = async () => {
      try {
        setLoading(true);
        const data = await ApiService.getWeeklyTrends();
        if (data.trends) {
          setTrends(data.trends);
        }
      } catch (err) {
        setError(err.message);
        console.error('Error fetching trends:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchTrends();
  }, []);

  const renderSkeleton = () => {
    return (
      <div className={layout.container}>
        <div className="mb-6">
          <div className="w-48 h-10 bg-gray-800 rounded animate-pulse"/>
        </div>
        
        {[...Array(5)].map((_, index) => (
          <div key={index} className={`${colors.bg.secondary} ${layout.card} p-6 mb-6`}>
            <div className="h-6 w-32 bg-gray-700 rounded animate-pulse mb-4"/>
            <div className="h-64 bg-gray-700 rounded animate-pulse"/>
          </div>
        ))}
      </div>
    );
  };

  if (loading) return renderSkeleton();
  if (error) return <div className="text-red-500">Error loading trends: {error}</div>;

  const renderSubredditGraph = (subreddit) => {
    const data = trends[subreddit] || [];

    const formattedData = data.map(item => ({
      ...item,
      date: new Date(item.date).toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
      }),
      downvotes: Math.abs(item.downvotes)  // Convert negative to positive
  }));
    
    return (
      <div key={subreddit} className={`${colors.bg.secondary} ${layout.card} p-6 mb-6`}>
        <h3 className={`${typography.subtitle} ${colors.text.primary} mb-4`}>
  <a 
    href={`https://reddit.com/r/${subreddit}`}
    target="_blank"
    rel="noopener noreferrer"
    className={`${typography.subtitle} ${colors.accent.primary} ${colors.accent.hover}`}
  >
    r/{subreddit}
  </a>
</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart 
            data={formattedData}
            margin={{ top: 10, right: 30, left: 20, bottom: 5 }}
            >
              <XAxis 
                dataKey="date" 
                stroke="#9CA3AF"  // Light gray text
                tick={{ fill: '#9CA3AF' }}
              />
<YAxis 
    stroke="#9CA3AF"
    tick={{ fill: '#9CA3AF' }}
    tickFormatter={(value) => `-${value}`}  // Optional: add any formatting you want
    label={{ 
        value: 'Downvotes',
        angle: -90,
        position: 'insideLeft',
        style: { fill: '#9CA3AF' }
    }}
/> 
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />      
              <Tooltip
                contentStyle={{ 
                    backgroundColor: '#1F2937', 
                    border: '1px solid #374151',
                    borderRadius: '0.375rem'
                  }}
                  labelStyle={{ color: '#9CA3AF' }}
                  itemStyle={{ color: '#F3F4F6' }}
                />
              <Line 
                type="monotone" 
                dataKey="downvotes" 
                stroke="#ff4444" 
                strokeWidth={2} 
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    );
  };

  if (loading) return <div>Loading trends...</div>;
  if (error) return <div>Error loading trends: {error}</div>;

  const categorySubreddits = categoryMap[selectedCategory]?.subreddits || [];

  return (
    <div className={layout.container}>
      <div className="mb-6">
        <select 
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="bg-gray-800 text-white p-2 rounded"
        >
          {Object.keys(categoryMap).map(category => (
            <option key={category} value={category}>
              {categoryMap[category].name}
            </option>
          ))}
        </select>
      </div>
      
      {categorySubreddits.map(subreddit => renderSubredditGraph(subreddit))}
    </div>
  );
}

export default TrendAnalysis;
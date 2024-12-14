import React from 'react';
import { colors } from '../styles/design-tokens';

function TabNavigation({ activeView, onViewChange }) {
  const views = {
    categories: {
      name: "Categories",
      key: "categories"
    },
    subreddits: {
      name: "Subreddit Totals",
      key: "subreddits"
    },
    trends: {
        name: "Weekly Trends",
        key: "trends"
    }
  };

  return (
    <div className="bg-gray-900 rounded-xl">
      <nav className="flex justify-center"> {/* Added justify-center */}
        {Object.values(views).map((view) => (
          <button
            key={view.key}
            onClick={() => onViewChange(view.key)}
            className={`py-4 px-6 text-sm font-medium focus:outline-none ${
              activeView === view.key
                ? 'text-white border-b-2 border-blue-500'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            {view.name}
          </button>
        ))}
      </nav>
    </div>
  );
}

export default TabNavigation;
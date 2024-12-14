import React from 'react';
import { layout } from '../styles/design-tokens';
import SubredditCard from './SubredditCard';


function SubredditTotals({ totals }) {
  return (
    <div className={layout.container}>
      {!totals ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="animate-pulse bg-gray-800 rounded-xl h-48"/>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {totals.map((total) => (
            <SubredditCard
              key={total.subreddit}
              subreddit={total.subreddit} 
              totalDownvotes={total.total_downvotes}
              commentCount={total.total_comments}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default SubredditTotals;
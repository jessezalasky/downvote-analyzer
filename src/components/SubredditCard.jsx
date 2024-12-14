import React from 'react';
import { colors, layout, typography } from '../styles/design-tokens';

function SubredditCard({ subreddit, totalDownvotes, commentCount }) {
  // Calculate average downvotes per comment
  const averageDownvotes = Math.abs(Math.round((totalDownvotes / commentCount) * 10) / 10);

  return (
    <div className={`
      ${colors.bg.secondary} 
      ${layout.card} 
      p-6
    `}>
      <div className="flex flex-col items-center text-center">
        {/* Score Display */}
        <span className={`
          ${typography.score} 
          ${colors.score.primary}
          mb-2
        `}>
          {totalDownvotes}
        </span>
        
        {/* Subreddit Name */}
        <a 
          href={`https://reddit.com/r/${subreddit}`}
          target="_blank"
          rel="noopener noreferrer"
          className={`${typography.subtitle} ${colors.accent.primary} ${colors.accent.hover}`}
        >
          r/{subreddit}
        </a>
        
        {/* Comment Count */}
        <span className={`
          ${typography.small} 
          ${colors.text.muted}
          mt-2
        `}>
          {commentCount} downvoted comments
        </span>

        {/* Average Downvotes */}
        <span className={`
          ${typography.small} 
          ${colors.text.muted}
          text-red-400
          mt-1
        `}>
          {averageDownvotes} downvotes per downvoted comment
        </span>
      </div>
    </div>
  );
}

export default SubredditCard;
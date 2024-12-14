import React from 'react';
import { colors, layout, typography } from '../styles/design-tokens';

function CategoryCard({ 
  category = '', 
  worstComment = {
    score: 0,
    body: 'No comments yet',
    subreddit: '',
    permalink: '#'
  }, 
  totalBelowThreshold = 0,
  onSeeMore = () => {} 
}) {
  const handleSeeMore = (e) => {
    e.preventDefault();
    onSeeMore();
  };

  return (
    <div className={`
      ${colors.bg.secondary} 
      ${layout.card} 
      p-6 
      h-[250px] 
      flex 
      flex-col 
      justify-between
    `}>
      {/* Header */}
      <div>
        <h3 className={`${typography.subtitle} ${colors.text.primary}`}>
          {category || 'Unknown Category'}
        </h3>
      </div>

      {/* Main Content */}
      <div className="flex gap-4 my-4">
        <div className="flex items-center justify-center w-16">
          <span className={`${typography.score} ${colors.score.primary}`}>
            {worstComment.score}
          </span>
        </div>
        <div className="flex-1">
          <p className={`${typography.body} ${colors.text.secondary} line-clamp-3`}>
            {worstComment.body}
          </p>
          <span className={`${typography.small} ${colors.text.muted} mt-2 block`}>
            {worstComment.subreddit ? `Worst Today: r/${worstComment.subreddit}` : 'No comments today'}
          </span>
        </div>
      </div>

      {/* Actions */}
      <div className={`
        flex 
        justify-start
        items-center 
        pt-4 
        border-t 
        ${colors.accent.border}
      `}>
        <button
          onClick={handleSeeMore}
          className={`
            ${typography.small} 
            ${colors.accent.primary} 
            ${colors.accent.hover}
            flex 
            items-center 
            gap-1
          `}
        >
          View More Downvoted Comments →
        </button>
      </div>
    </div>
  );
}

export default CategoryCard;
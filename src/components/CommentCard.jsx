import React from 'react';
import { colors, layout, typography } from '../styles/design-tokens';

function CommentCard({ comment, isFirst = false }) {
  return (
    <div className={`
      ${colors.bg.tertiary} 
      ${layout.card} 
      p-6
      w-full
      ${isFirst ? 'border-l-4 border-red-500' : ''}
    `}>
      <div className="flex gap-6 w-full"> {/* Increased gap for better spacing */}
        <div className="flex-shrink-0 w-20 text-center"> {/* Increased width for score */}
          <span className={`
            ${isFirst ? 'text-3xl' : 'text-2xl'} 
            font-bold 
            ${colors.score.primary}
          `}>
            {comment.score}
          </span>
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-2">
            <span className={`${typography.small} ${colors.text.muted}`}>Posted by</span>
            <span className={`${typography.small} font-medium text-gray-200`}>u/{comment.author}</span>
            <span className={`${typography.small} ${colors.text.muted}`}>in</span>
            <a 
              href={`https://reddit.com/r/${comment.subreddit}`}
              target="_blank"
              rel="noopener noreferrer"
              className={`${typography.small} font-medium text-blue-400 hover:text-blue-300`}
            >
              r/{comment.subreddit}
            </a>
          </div>
          
          <p className={`${typography.body} ${colors.text.secondary} break-words w-full overflow-hidden`}>
            {comment.body}
          </p>
          
          <div className="mt-4 flex justify-between items-center gap-4">
            <span className={`${typography.small} ${colors.text.muted}`}>
              {new Date(comment.created_utc).toLocaleDateString()}
            </span>
            <a
              href={comment.permalink}
              target="_blank"
              rel="noopener noreferrer"
              className={`${typography.small} text-blue-400 hover:text-blue-300 flex items-center gap-1`}
            >
              View on Reddit&nbsp;→
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}

export default CommentCard;
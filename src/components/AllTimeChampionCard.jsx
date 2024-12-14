import React from 'react';
import { colors, layout, typography } from "../styles/design-tokens";

function AllTimeChampionCard({ champion }) {
  if (!champion) return null;

  return (
    <div className={`${colors.bg.secondary} ${layout.card} p-6 ${layout.spacing.section}`}>
      <div className={layout.spacing.element}>
        <h2 className={`${typography.title} ${colors.text.primary}`}>
          Most Downvoted Comment Discovered
        </h2>
        <div className="h-1 w-20 bg-red-500"></div>
      </div>

      <div className="flex gap-6">
        {/* Score Display */}
        <div className="flex flex-col items-center justify-center w-24">
          <span className={`${typography.score} ${colors.score.primary}`}>
            {champion.score}
          </span>
        </div>

        {/* Content */}
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-3">
            <span className={`${typography.small} ${colors.text.muted}`}>Posted by</span>
            <span className={`${typography.small} ${colors.text.secondary}`}>
              u/{champion.author}
            </span>
            <span className={`${typography.small} ${colors.text.muted}`}>in</span>
            <a 
              href={`https://reddit.com/r/${champion.subreddit}`}
              className={`${typography.small} ${colors.accent.primary} ${colors.accent.hover}`}
            >
              r/{champion.subreddit}
            </a>
          </div>

          <p className={`${typography.body} ${colors.text.secondary} leading-relaxed mb-4`}>
            {champion.body}
          </p>
        </div>
      </div>

      <div className={`mt-4 pt-4 border-t ${colors.accent.border} flex justify-between items-center`}>
        <span className={`${typography.small} ${colors.text.muted}`}>
          {new Date(champion.created_utc).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
          })}
        </span>
        <a 
          href={champion.permalink}
          target="_blank"
          rel="noopener noreferrer"
          className={`${typography.small} ${colors.accent.primary} ${colors.accent.hover} flex items-center gap-1`}
        >
          View on Reddit →
        </a>
      </div>
    </div>
  );
}

export default AllTimeChampionCard;
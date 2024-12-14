import React from 'react';
import { colors, layout, typography } from "../styles/design-tokens";

function AllTimeSubredditTotals({ totals }) {
  if (!totals) {
    return (
      <div className={`${colors.bg.secondary} ${layout.card} p-6 ${layout.spacing.section}`}>
        <div className={layout.spacing.element}>
          <h2 className={`${typography.title} ${colors.text.primary}`}>
            Comment Downvotes by Subreddit Leaderboard
          </h2>
          <div className="h-1 w-20 bg-red-500"/>
        </div>
        <div className="space-y-4">
          {[...Array(5)].map((_, index) => (
            <div key={index} className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="h-6 w-6 bg-gray-700 rounded animate-pulse"/>
                <div className="h-6 w-32 bg-gray-700 rounded animate-pulse"/>
              </div>
              <div className="h-6 w-20 bg-gray-700 rounded animate-pulse"/>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (totals.length === 0) {
    return (
      <div className={`${colors.bg.secondary} ${layout.card} p-6 ${layout.spacing.section}`}>
        <div className={layout.spacing.element}>
          <h2 className={`${typography.title} ${colors.text.primary}`}>
            Comment Downvotes by Subreddit Leaderboard
          </h2>
          <div className="h-1 w-20 bg-red-500"/>
        </div>
        <div className={`${typography.body} ${colors.text.secondary} text-center py-4`}>
          No subreddit data available.
        </div>
      </div>
    );
  }

  return (
    <div className={`${colors.bg.secondary} ${layout.card} p-6 ${layout.spacing.section}`}>
      <div className={layout.spacing.element}>
        <h2 className={`${typography.title} ${colors.text.primary}`}>
          Comment Downvotes by Subreddit Leaderboard
        </h2>
        <div className="h-1 w-20 bg-red-500"/>
      </div>
      <div className="space-y-4">
        {totals.slice(0, 5).map((total, index) => (
          <div key={total.subreddit} className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className={`${typography.subtitle} ${colors.text.muted}`}>
                #{index + 1}
              </span>
              <a
                href={`https://reddit.com/r/${total.subreddit}`}
                target="_blank"
                rel="noopener noreferrer"
                className={`${typography.subtitle} ${colors.accent.primary} ${colors.accent.hover}`}
              >
                r/{total.subreddit}
              </a>
            </div>
            <span className={`${typography.subtitle} ${colors.score.primary}`}>
              {total.all_time_downvotes}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default AllTimeSubredditTotals;
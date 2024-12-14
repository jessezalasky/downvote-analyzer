import React from 'react';
import { colors, layout, typography } from '../styles/design-tokens';
import CommentCard from './CommentCard';

function CategoryModal({ isOpen, onClose, category, comments }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div className={`
        ${colors.bg.secondary}
        ${layout.card}
        w-full
        max-w-4xl
        max-h-[80vh]
        mx-4
        relative
        overflow-hidden
      `}>
        {/* Header */}
        <div className="p-6 border-b border-gray-800">
          <div className="flex justify-between items-center">
            <h2 className={`${typography.title} ${colors.text.primary}`}>
              {category} - Most Downvoted Today
            </h2>
            <button
              onClick={onClose}
              className={`${colors.text.muted} hover:${colors.text.primary} text-2xl`}
            >
              ×
            </button>
          </div>
        </div>

{/* Scrollable Content */}
<div className="overflow-y-auto p-6 max-h-[calc(80vh-120px)]">
  {comments.map((comment, index) => (
    <div 
      key={comment.comment_id}
      className={`${index !== 0 ? 'mt-6' : ''}`}
    >
      <CommentCard 
        comment={comment} 
        isFirst={index === 0}
      />
    </div>
  ))}
</div>
      </div>
    </div>
  );
}

export default CategoryModal;
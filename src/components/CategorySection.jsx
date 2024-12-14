import React, { useState } from 'react';
import { colors, layout } from '../styles/design-tokens.js';
import CategoryCard from './CategoryCard';
import CategoryModal from './CategoryModal';
import ApiService from '../services/api';

function CategorySection({ categories = {}, comments = {} }) {
  const [selectedCategory, setSelectedCategory] = useState(null);
  
  const handleOpenModal = (category) => {
    setSelectedCategory(category);
  };

  const handleCloseModal = () => {
    setSelectedCategory(null);
  };

  const getCommentsForCategory = (categoryName) => {
    if (!comments || !categoryName) return [];
    return comments[categoryName] || [];
  };

  const getWorstComment = (categoryName) => {
    const categoryComments = getCommentsForCategory(categoryName);
    return categoryComments.length > 0 ? categoryComments[0] : {
      score: 0,
      body: 'No comments yet',
      subreddit: '',
      permalink: '#'
    };
  };

  // Sort categories by their worst comment's score
  const sortedCategories = Object.entries(categories || {}).sort((a, b) => {
    const aWorstScore = getWorstComment(a[0]).score;
    const bWorstScore = getWorstComment(b[0]).score;
    return aWorstScore - bWorstScore; // Most negative (worst) first
  });

  return (
    <div className={layout.container}>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {sortedCategories.map(([categoryName, categoryData]) => (
          <CategoryCard
            key={categoryName}
            category={categoryName}
            worstComment={getWorstComment(categoryName)}
            onSeeMore={() => handleOpenModal(categoryName)}
          />
        ))}
      </div>

      <CategoryModal
        isOpen={selectedCategory !== null}
        onClose={handleCloseModal}
        category={selectedCategory}
        comments={selectedCategory ? getCommentsForCategory(selectedCategory) : []}
      />
    </div>
  );
}

export default CategorySection;
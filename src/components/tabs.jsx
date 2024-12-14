import React from 'react';

function Tabs({ categories, activeTab, onTabChange }) {
    return (
      <div className="bg-gray-900">  {/* Removed rounded-t-lg */}
        <nav className="flex">
          {Object.keys(categories).map((category) => (
            <button
              key={category}
              onClick={() => onTabChange(category)}
              className={`py-4 px-6 text-sm font-medium focus:outline-none ${
                activeTab === category
                  ? 'text-white border-b-2 border-blue-500'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              {categories[category].name}
            </button>
          ))}
        </nav>
      </div>
    );
  }
  
  export default Tabs;
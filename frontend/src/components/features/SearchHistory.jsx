import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Search, Clock, TrendingUp, Trash2 } from 'lucide-react';
import { storageService } from '../../services/storage';
import { formatDate, formatTime } from '../../utils/helpers';
import toast from 'react-hot-toast';

const SearchHistory = ({ onSelectHistory }) => {
  const [history, setHistory] = useState([]);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = () => {
    const searchHistory = storageService.getSearchHistory();
    setHistory(searchHistory);
  };

  const clearHistory = () => {
    if (window.confirm('Clear all search history?')) {
      localStorage.removeItem('searchHistory');
      setHistory([]);
      toast.success('Search history cleared', {
        icon: '🗑️',
        style: {
          borderRadius: '12px',
          background: '#333',
          color: '#fff',
        },
      });
    }
  };

  const removeItem = (index) => {
    const updated = history.filter((_, i) => i !== index);
    localStorage.setItem('searchHistory', JSON.stringify(updated));
    setHistory(updated);
    toast.success('Removed from history', {
      icon: '✓',
      style: {
        borderRadius: '12px',
        background: '#333',
        color: '#fff',
      },
    });
  };

  const handleSelect = (item) => {
    if (onSelectHistory) {
      onSelectHistory(item);
    }
    setIsOpen(false);
    toast.success('Search loaded', {
      icon: '🔍',
      style: {
        borderRadius: '12px',
        background: '#333',
        color: '#fff',
      },
    });
  };

  return (
    <div className="relative">
      {/* Toggle Button */}
      <motion.button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2.5 bg-white dark:bg-gray-800 border-2 border-gray-200 dark:border-gray-700 rounded-xl hover:border-primary-400 dark:hover:border-primary-600 transition-all duration-200 shadow-sm hover:shadow-md"
        whileHover={{ scale: 1.02, y: -1 }}
        whileTap={{ scale: 0.98 }}
      >
        <Clock className="w-5 h-5 text-gray-600 dark:text-gray-400" />
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">History</span>
        {history.length > 0 && (
          <motion.span 
            className="px-2 py-0.5 bg-gradient-to-r from-primary-100 to-purple-100 dark:from-primary-900/50 dark:to-purple-900/50 text-primary-700 dark:text-primary-300 text-xs rounded-full font-semibold"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", stiffness: 500 }}
          >
            {history.length}
          </motion.span>
        )}
      </motion.button>

      {/* History Dropdown */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ type: "spring", stiffness: 300, damping: 25 }}
            className="absolute top-full mt-2 right-0 w-96 bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 z-50 max-h-[500px] overflow-hidden flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-primary-50 to-purple-50 dark:from-primary-900/20 dark:to-purple-900/20">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-primary-600 dark:text-primary-400" />
                <h3 className="font-bold text-gray-900 dark:text-gray-100">Search History</h3>
              </div>
              {history.length > 0 && (
                <motion.button
                  onClick={clearHistory}
                  className="flex items-center gap-1.5 text-sm text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 font-medium px-3 py-1.5 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Trash2 className="w-4 h-4" />
                  Clear All
                </motion.button>
              )}
            </div>

            {/* History List */}
            <div className="overflow-y-auto">
              {history.length === 0 ? (
                <motion.div 
                  className="p-12 text-center"
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.1 }}
                >
                  <motion.div
                    animate={{ 
                      y: [0, -10, 0],
                    }}
                    transition={{ 
                      duration: 2, 
                      repeat: Infinity,
                      ease: "easeInOut" 
                    }}
                  >
                    <Search className="w-16 h-16 mx-auto mb-3 text-gray-300 dark:text-gray-600" />
                  </motion.div>
                  <p className="text-gray-500 dark:text-gray-400 font-medium">No search history yet</p>
                  <p className="text-gray-400 dark:text-gray-500 text-sm mt-1">Your recent searches will appear here</p>
                </motion.div>
              ) : (
                <div className="divide-y divide-gray-100 dark:divide-gray-700">
                  {history.map((item, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20 }}
                      transition={{ delay: index * 0.03 }}
                      className="p-4 hover:bg-gradient-to-r hover:from-primary-50 hover:to-purple-50 dark:hover:from-primary-900/10 dark:hover:to-purple-900/10 cursor-pointer group relative transition-all duration-200"
                      onClick={() => handleSelect(item)}
                      whileHover={{ x: 4 }}
                    >
                      <div className="pr-10">
                        <div className="flex items-start gap-2 mb-2">
                          <Clock className="w-4 h-4 text-gray-400 dark:text-gray-500 mt-0.5 flex-shrink-0" />
                          <p className="font-medium text-gray-900 dark:text-gray-100 line-clamp-2">
                            {item.query || item.symptoms}
                          </p>
                        </div>
                        <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 ml-6">
                          <span>{formatDate(item.timestamp)}</span>
                          <span>•</span>
                          <span>{formatTime(item.timestamp)}</span>
                          {item.type && (
                            <>
                              <span>•</span>
                              <span className="px-2 py-0.5 bg-gradient-to-r from-primary-100 to-purple-100 dark:from-primary-900/50 dark:to-purple-900/50 text-primary-700 dark:text-primary-300 rounded-full font-medium">
                                {item.type}
                              </span>
                            </>
                          )}
                        </div>
                      </div>
                      <motion.button
                        onClick={(e) => {
                          e.stopPropagation();
                          removeItem(index);
                        }}
                        className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity p-1.5 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-lg"
                        whileHover={{ scale: 1.1, rotate: 90 }}
                        whileTap={{ scale: 0.9 }}
                      >
                        <X className="w-4 h-4 text-red-600 dark:text-red-400" />
                      </motion.button>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
};

export default SearchHistory;

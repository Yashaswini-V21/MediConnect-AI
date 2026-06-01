import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Heart, Trash2, ArrowRight, Sparkles } from 'lucide-react';
import { storageService } from '../../services/storage';
import HospitalCard from './HospitalCard';
import { useLanguage } from '../../context/LanguageContext';
import toast from 'react-hot-toast';

const Favorites = () => {
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(true);
  const { } = useLanguage(); // keep context for future i18n use

  useEffect(() => {
    loadFavorites();
  }, []);

  const loadFavorites = () => {
    setLoading(true);
    setTimeout(() => {
      const favs = storageService.getFavorites();
      setFavorites(favs);
      setLoading(false);
    }, 300);
  };

  const removeFavorite = (hospitalId) => {
    storageService.removeFavorite(hospitalId);
    loadFavorites();
    toast.success('Removed from favorites', {
      icon: '💔',
      style: {
        borderRadius: '12px',
        background: '#333',
        color: '#fff',
      },
    });
  };

  const isFavorite = (hospitalId) => {
    return favorites.some(fav => fav.id === hospitalId);
  };

  const handleFavoriteToggle = (hospital) => {
    if (isFavorite(hospital.id)) {
      removeFavorite(hospital.id);
    } else {
      storageService.addFavorite(hospital);
      loadFavorites();
      toast.success('Added to favorites!', {
        icon: '❤️',
        style: {
          borderRadius: '12px',
          background: '#333',
          color: '#fff',
        },
      });
    }
  };

  const clearAllFavorites = () => {
    if (window.confirm('Are you sure you want to remove all favorites?')) {
      localStorage.removeItem('favorites');
      loadFavorites();
      toast.success('All favorites cleared', {
        icon: '🗑️',
        style: {
          borderRadius: '12px',
          background: '#333',
          color: '#fff',
        },
      });
    }
  };

  // Loading skeleton
  if (loading) {
    return (
      <div className="container mx-auto px-4 py-12">
        <div className="animate-pulse">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-14 h-14 bg-gray-200 dark:bg-gray-700 rounded-xl"></div>
            <div>
              <div className="h-10 w-64 bg-gray-200 dark:bg-gray-700 rounded-xl mb-2"></div>
              <div className="h-4 w-32 bg-gray-200 dark:bg-gray-700 rounded-xl"></div>
            </div>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-64 bg-gray-200 dark:bg-gray-700 rounded-2xl"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-8 gap-4">
          <motion.div 
            className="flex items-center gap-3"
            initial={{ x: -20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.1 }}
          >
            <motion.div 
              className="p-3 bg-gradient-to-br from-red-100 to-pink-100 dark:from-red-900/30 dark:to-pink-900/30 rounded-xl"
              whileHover={{ scale: 1.05, rotate: 5 }}
              whileTap={{ scale: 0.95 }}
            >
              <Heart className="w-8 h-8 text-red-600 dark:text-red-400 fill-red-600 dark:fill-red-400" />
            </motion.div>
            <div>
              <h1 className="text-3xl sm:text-4xl font-bold bg-gradient-to-r from-primary-600 to-purple-600 bg-clip-text text-transparent">
                Favorite Hospitals
              </h1>
              <motion.p 
                className="text-gray-600 dark:text-gray-400 mt-1"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2 }}
              >
                {favorites.length} {favorites.length === 1 ? 'hospital' : 'hospitals'} saved
              </motion.p>
            </div>
          </motion.div>
          
          {favorites.length > 0 && (
            <motion.button
              onClick={clearAllFavorites}
              className="flex items-center gap-2 px-4 py-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-xl transition-all duration-200 border-2 border-transparent hover:border-red-200 dark:hover:border-red-800"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              initial={{ x: 20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: 0.1 }}
            >
              <Trash2 className="w-5 h-5" />
              <span className="font-medium">Clear All</span>
            </motion.button>
          )}
        </div>

        {/* Empty State */}
        <AnimatePresence mode="wait">
          {favorites.length === 0 ? (
            <motion.div
              key="empty"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ duration: 0.3 }}
              className="card text-center py-16 relative overflow-hidden"
            >
              {/* Background decoration */}
              <div className="absolute inset-0 opacity-5">
                <div className="absolute top-10 left-10 w-32 h-32 bg-primary-500 rounded-full blur-3xl"></div>
                <div className="absolute bottom-10 right-10 w-40 h-40 bg-purple-500 rounded-full blur-3xl"></div>
              </div>
              
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
              >
                <Heart className="w-20 h-20 mx-auto mb-4 text-gray-300 dark:text-gray-600" />
              </motion.div>
              
              <motion.h3 
                className="text-2xl font-bold text-gray-400 dark:text-gray-500 mb-2"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
              >
                No Favorites Yet
              </motion.h3>
              
              <motion.p 
                className="text-gray-500 dark:text-gray-400 mb-6 max-w-md mx-auto"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
              >
                Start building your list of trusted hospitals for quick access during emergencies
              </motion.p>
              
              <motion.a
                href="/hospitals"
                className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-primary-600 to-purple-600 text-white rounded-xl hover:from-primary-700 hover:to-purple-700 transition-all duration-200 font-medium shadow-lg hover:shadow-xl"
                whileHover={{ scale: 1.05, y: -2 }}
                whileTap={{ scale: 0.95 }}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
              >
                <Sparkles className="w-5 h-5" />
                Find Hospitals
                <ArrowRight className="w-5 h-5" />
              </motion.a>
            </motion.div>
          ) : (
            /* Favorites Grid */
            <motion.div 
              key="grid"
              className="grid md:grid-cols-2 lg:grid-cols-3 gap-6"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
            >
              <AnimatePresence>
                {favorites.map((hospital, index) => (
                  <motion.div
                    key={hospital.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    transition={{ delay: index * 0.05 }}
                    whileHover={{ y: -5 }}
                  >
                    <HospitalCard
                      hospital={hospital}
                      isFavorite={true}
                      onFavorite={handleFavoriteToggle}
                    />
                  </motion.div>
                ))}
              </AnimatePresence>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
};

export default Favorites;

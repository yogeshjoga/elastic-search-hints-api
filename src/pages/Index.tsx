
import React, { useState, useCallback } from 'react';
import SearchBar from '../components/SearchBar';
import SearchResults from '../components/SearchResults';
import { useQuery } from '@tanstack/react-query';

const Index = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSuggestion, setSelectedSuggestion] = useState('');
  const [showResults, setShowResults] = useState(false);

  // Search function connecting to your Python backend
  const searchClothing = async (query: string): Promise<any> => {
    if (!query.trim()) return null;
    
    console.log(`Searching for: ${query}`);
    const response = await fetch(`http://localhost:8000/search_by_prompt_or_query?q=${encodeURIComponent(query)}&size=20`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    console.log('Search response:', data);
    return data;
  };

  // Use React Query for search
  const { data: searchResults, isLoading, error, refetch } = useQuery({
    queryKey: ['search', selectedSuggestion || searchQuery],
    queryFn: () => searchClothing(selectedSuggestion || searchQuery),
    enabled: false, // We'll trigger manually
  });

  // Handle search submission
  const handleSearch = useCallback((query: string) => {
    if (query.trim()) {
      setSearchQuery(query);
      setSelectedSuggestion('');
      setShowResults(true);
      refetch();
    }
  }, [refetch]);

  // Handle suggestion selection
  const handleSuggestionSelect = useCallback((suggestion: string) => {
    setSelectedSuggestion(suggestion);
    setSearchQuery(suggestion);
    setShowResults(true);
    refetch();
  }, [refetch]);

  // Handle search clear
  const handleClearSearch = useCallback(() => {
    setSearchQuery('');
    setSelectedSuggestion('');
    setShowResults(false);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-slate-200/60 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-xl flex items-center justify-center">
                <span className="text-white font-bold text-lg">C</span>
              </div>
              <div>
                <h1 className="text-xl font-semibold text-slate-900">ClothingSearch</h1>
                <p className="text-sm text-slate-600">Professional Fashion Discovery</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {!showResults ? (
          /* Landing Page */
          <div className="text-center py-20">
            <div className="max-w-3xl mx-auto">
              <h1 className="text-5xl font-bold text-slate-900 mb-6 leading-tight">
                Discover Your Perfect
                <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent block">
                  Fashion Style
                </span>
              </h1>
              <p className="text-xl text-slate-600 mb-12 leading-relaxed">
                Search through our extensive collection of clothing with intelligent suggestions
                and precise matching powered by Elasticsearch.
              </p>
              
              <div className="max-w-2xl mx-auto">
                <SearchBar
                  onSearch={handleSearch}
                  onSuggestionSelect={handleSuggestionSelect}
                  placeholder="Search for clothing styles, colors, brands..."
                />
              </div>
            </div>
          </div>
        ) : (
          /* Search Results Page */
          <div>
            <div className="mb-8">
              <div className="flex items-center justify-between mb-4">
                <button
                  onClick={handleClearSearch}
                  className="flex items-center space-x-2 text-slate-600 hover:text-slate-900 transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                  <span>Back to Search</span>
                </button>
              </div>
              
              <div className="max-w-2xl">
                <SearchBar
                  onSearch={handleSearch}
                  onSuggestionSelect={handleSuggestionSelect}
                  initialValue={searchQuery}
                  placeholder="Search for clothing styles, colors, brands..."
                />
              </div>
            </div>

            <SearchResults
              results={searchResults}
              isLoading={isLoading}
              error={error}
              searchQuery={selectedSuggestion || searchQuery}
            />
          </div>
        )}
      </main>
    </div>
  );
};

export default Index;

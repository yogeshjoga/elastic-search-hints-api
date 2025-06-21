
import React from 'react';
import { Loader2, Search, AlertCircle, TrendingUp } from 'lucide-react';

interface SearchResult {
  prompt: string;
  query: string;
  score: number;
  match_percentage: number;
  highlight?: {
    prompt?: string[];
    query?: string[];
  };
}

interface SearchResultsProps {
  results?: {
    hits: SearchResult[];
    total: number;
    took: number;
  };
  isLoading: boolean;
  error: any;
  searchQuery: string;
}

const SearchResults: React.FC<SearchResultsProps> = ({
  results,
  isLoading,
  error,
  searchQuery
}) => {
  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-lg text-slate-600">Searching for "{searchQuery}"...</p>
          <p className="text-sm text-slate-500 mt-1">Finding the best matches for you</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-center max-w-md">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-900 mb-2">Search Error</h3>
          <p className="text-slate-600 mb-4">
            We encountered an issue while searching. Please check if the Elasticsearch service is running.
          </p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  // No results
  if (!results || results.hits.length === 0) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-center max-w-md">
          <Search className="h-12 w-12 text-slate-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-900 mb-2">No Results Found</h3>
          <p className="text-slate-600 mb-4">
            We couldn't find any clothing items matching "{searchQuery}". Try different keywords or check your spelling.
          </p>
          <div className="text-sm text-slate-500">
            <p>Search tips:</p>
            <ul className="list-disc list-inside mt-2 space-y-1">
              <li>Try broader terms like "dress" or "shirt"</li>
              <li>Check for typos in your search</li>
              <li>Use different keywords or synonyms</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  // Highlight text helper
  const highlightText = (text: string, highlights?: string[]) => {
    if (!highlights || highlights.length === 0) return text;
    
    const highlighted = highlights[0];
    const parts = highlighted.split(/<\/?em>/g);
    
    return (
      <span>
        {parts.map((part, index) => 
          index % 2 === 1 ? (
            <mark key={index} className="bg-yellow-200 px-1 rounded">
              {part}
            </mark>
          ) : (
            <span key={index}>{part}</span>
          )
        )}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Results Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">
            Search Results for "{searchQuery}"
          </h2>
          <p className="text-slate-600 mt-1">
            Found {results.total.toLocaleString()} results in {results.took}ms
          </p>
        </div>
        <div className="text-right">
          <div className="flex items-center space-x-2 text-sm text-slate-500">
            <TrendingUp className="h-4 w-4" />
            <span>Sorted by relevance</span>
          </div>
        </div>
      </div>

      {/* Results Grid */}
      <div className="grid gap-6">
        {results.hits.map((result, index) => (
          <div
            key={index}
            className="bg-white/80 backdrop-blur-sm rounded-2xl border border-slate-200/60 hover:border-blue-200 hover:shadow-lg transition-all duration-200 overflow-hidden"
          >
            <div className="p-6">
              {/* Match Score */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center">
                    <span className="text-white font-bold text-lg">
                      {result.match_percentage}%
                    </span>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-slate-900">Match Score</div>
                    <div className="text-xs text-slate-500">Relevance: {result.score.toFixed(2)}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-slate-500">Result #{index + 1}</div>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="w-full bg-slate-200 rounded-full h-2 mb-6">
                <div
                  className="bg-gradient-to-r from-blue-500 to-indigo-600 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${result.match_percentage}%` }}
                ></div>
              </div>

              {/* Content */}
              <div className="space-y-4">
                {/* Prompt */}
                <div className="bg-slate-50/80 rounded-xl p-4">
                  <div className="text-sm font-medium text-slate-700 mb-2">Prompt</div>
                  <div className="text-slate-900 leading-relaxed">
                    {result.highlight?.prompt 
                      ? highlightText(result.prompt, result.highlight.prompt)
                      : result.prompt
                    }
                  </div>
                </div>

                {/* Query */}
                <div className="bg-blue-50/80 rounded-xl p-4">
                  <div className="text-sm font-medium text-blue-700 mb-2">Query</div>
                  <div className="text-slate-900 leading-relaxed">
                    {result.highlight?.query 
                      ? highlightText(result.query, result.highlight.query)
                      : result.query
                    }
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-end space-x-3 mt-6 pt-4 border-t border-slate-200/60">
                <button className="px-4 py-2 text-sm text-slate-600 hover:text-slate-900 transition-colors">
                  View Details
                </button>
                <button className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors">
                  Select Item
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Pagination placeholder */}
      {results.hits.length > 0 && (
        <div className="flex items-center justify-center pt-8">
          <div className="text-sm text-slate-500">
            Showing {results.hits.length} of {results.total} results
          </div>
        </div>
      )}
    </div>
  );
};

export default SearchResults;

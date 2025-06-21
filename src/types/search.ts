
export interface SearchResult {
  prompt: string;
  query: string;
  score: number;
  match_percentage: number;
  highlight?: {
    prompt?: string[];
    query?: string[];
  };
}

export interface SearchResponse {
  hits: SearchResult[];
  total: number;
  took: number;
}

export interface AutocompleteSuggestion {
  text: string;
  type: 'prompt' | 'query';
}

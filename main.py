from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from elasticsearch import Elasticsearch
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Elasticsearch Auto-Suggestions API",
    description="FastAPI service for searching Elasticsearch data with auto-suggestions",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Elasticsearch configuration
ES_HOST = "localhost"
ES_PORT = 32768
INDEX_NAME = "clothing_prompts"

# Initialize Elasticsearch client
try:
    es = Elasticsearch([f"http://{ES_HOST}:{ES_PORT}"])
    logger.info(f"Connected to Elasticsearch at {ES_HOST}:{ES_PORT}")
except Exception as e:
    logger.error(f"Failed to connect to Elasticsearch: {e}")
    es = None

# Pydantic models
class SearchResult(BaseModel):
    prompt: str
    query: str
    score: Optional[float] = None
    match_percentage: Optional[int] = None
    highlight: Optional[Dict[str, Any]] = None

class SearchResponse(BaseModel):
    total: int
    hits: List[SearchResult]
    took: int
    suggestions: List[str] = []

class HealthResponse(BaseModel):
    status: str
    elasticsearch_connected: bool
    cluster_name: Optional[str] = None
    cluster_health: Optional[str] = None

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint to verify API and Elasticsearch connectivity"""
    if not es:
        return HealthResponse(
            status="unhealthy",
            elasticsearch_connected=False
        )
    
    try:
        cluster_info = es.info()
        cluster_health = es.cluster.health()
        
        return HealthResponse(
            status="healthy",
            elasticsearch_connected=True,
            cluster_name=cluster_info.get("cluster_name"),
            cluster_health=cluster_health.get("status")
        )
    except Exception as e:
        logger.error(f"Elasticsearch health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            elasticsearch_connected=False
        )

# Search endpoint with auto-suggestions
@app.get("/search", response_model=SearchResponse)
async def search_documents(
    q: str = Query(..., description="Search query", min_length=1),
    size: int = Query(10, description="Number of results to return", ge=1, le=100),
    suggest: bool = Query(True, description="Include auto-suggestions"),
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to search")
):
    """
    Search documents in Elasticsearch with auto-suggestions
    
    - **q**: Search query (required)
    - **size**: Number of results to return (default: 10, max: 100)
    - **suggest**: Whether to include auto-suggestions (default: True)
    - **fields**: Specific fields to search (optional, searches all fields by default)
    """
    
    if not es:
        raise HTTPException(status_code=503, detail="Elasticsearch connection not available")
    
    try:
        # Build the search query
        search_body = {
            "size": size,
            "query": {
                "multi_match": {
                    "query": q,
                    "fields": ["prompt^2", "query^1.5", "_all"],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            },
            "highlight": {
                "fields": {
                    "prompt": {},
                    "query": {}
                },
                "pre_tags": ["<mark>"],
                "post_tags": ["</mark>"]
            }
        }
        
        # Add field-specific search if specified
        if fields:
            field_list = [field.strip() for field in fields.split(",")]
            search_body["query"]["multi_match"]["fields"] = field_list
        
        # Add suggestions if requested
        if suggest:
            search_body["suggest"] = {
                "prompt_suggest": {
                    "text": q,
                    "term": {
                        "field": "prompt",
                        "size": 5
                    }
                },
                "query_suggest": {
                    "text": q,
                    "term": {
                        "field": "query",
                        "size": 5
                    }
                }
            }
        
        # Execute search
        response = es.search(index=INDEX_NAME, body=search_body)
        
        # Process results
        hits = []
        for hit in response["hits"]["hits"]:
            doc = {
                "id": hit["_id"],
                "score": hit["_score"],
                "source": hit["_source"]
            }
            
            # Add highlights if available
            if "highlight" in hit:
                doc["highlight"] = hit["highlight"]
            
            hits.append(doc)
        
        # Process suggestions
        suggestions = []
        if suggest and "suggest" in response:
            for suggest_type in ["prompt_suggest", "query_suggest"]:
                if suggest_type in response["suggest"]:
                    for suggestion in response["suggest"][suggest_type]:
                        for option in suggestion.get("options", []):
                            if option["text"] not in suggestions:
                                suggestions.append(option["text"])
        
        return SearchResponse(
            total=response["hits"]["total"]["value"],
            hits=hits,
            took=response["took"],
            suggestions=suggestions[:10]  # Limit suggestions to 10
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# Auto-complete endpoint for search suggestions
@app.get("/autocomplete")
async def autocomplete(
    q: str = Query(..., description="Partial search query", min_length=1),
    size: int = Query(5, description="Number of suggestions to return", ge=1, le=10)
):
    """
    Get auto-complete suggestions based on partial input
    """
    
    if not es:
        raise HTTPException(status_code=503, detail="Elasticsearch connection not available")
    
    try:
        # Use completion suggester or prefix query
        search_body = {
            "size": 0,
            "suggest": {
                "autocomplete": {
                    "text": q,
                    "completion": {
                        "field": "prompt.suggest",  # Assuming you have a completion field
                        "size": size
                    }
                }
            }
        }
        
        # Fallback to prefix query if completion suggester is not available
        fallback_body = {
            "size": size,
            "query": {
                "bool": {
                    "should": [
                        {
                            "prefix": {
                                "prompt": {
                                    "value": q.lower()
                                }
                            }
                        },
                        {
                            "prefix": {
                                "query": {
                                    "value": q.lower()
                                }
                            }
                        }
                    ]
                }
            },
            "_source": ["prompt", "query"]
        }
        
        try:
            # Try completion suggester first
            response = es.search(index=INDEX_NAME, body=search_body)
            suggestions = []
            
            if "suggest" in response and "autocomplete" in response["suggest"]:
                for suggestion in response["suggest"]["autocomplete"]:
                    for option in suggestion.get("options", []):
                        suggestions.append(option["text"])
            
            if not suggestions:
                # Fallback to prefix query
                response = es.search(index=INDEX_NAME, body=fallback_body)
                suggestions = []
                
                for hit in response["hits"]["hits"]:
                    source = hit["_source"]
                    if "prompt" in source and source["prompt"] not in suggestions:
                        suggestions.append(source["prompt"])
                    if "query" in source and source["query"] not in suggestions:
                        suggestions.append(source["query"])
            
            return {"suggestions": suggestions[:size]}
            
        except Exception:
            # Use fallback method
            response = es.search(index=INDEX_NAME, body=fallback_body)
            suggestions = []
            
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                if "prompt" in source and source["prompt"] not in suggestions:
                    suggestions.append(source["prompt"])
                if "query" in source and source["query"] not in suggestions:
                    suggestions.append(source["query"])
            
            return {"suggestions": suggestions[:size]}
        
    except Exception as e:
        logger.error(f"Autocomplete failed: {e}")
        raise HTTPException(status_code=500, detail=f"Autocomplete failed: {str(e)}")

# Get all indices endpoint
@app.get("/indices")
async def get_indices():
    """Get all available Elasticsearch indices"""
    
    if not es:
        raise HTTPException(status_code=503, detail="Elasticsearch connection not available")
    
    try:
        indices = es.indices.get_alias(index="*")
        return {"indices": list(indices.keys())}
    except Exception as e:
        logger.error(f"Failed to get indices: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get indices: {str(e)}")

# Get index mapping endpoint
@app.get("/mapping/{index_name}")
async def get_index_mapping(index_name: str):
    """Get mapping for a specific index"""
    
    if not es:
        raise HTTPException(status_code=503, detail="Elasticsearch connection not available")
    
    try:
        mapping = es.indices.get_mapping(index=index_name)
        return {"mapping": mapping}
    except Exception as e:
        logger.error(f"Failed to get mapping for {index_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get mapping: {str(e)}")

# Search by prompt or query
@app.get("/search_by_prompt_or_query", response_model=SearchResponse)
async def search_by_prompt_or_query(q: str, size: int = 10):
    """
    Search for documents matching either the prompt or query fields.
    Returns results with both prompt and query fields, along with highlights.
    """
    if not es or not es.ping():
        raise HTTPException(status_code=503, detail="Elasticsearch is not available")
    
    try:
        # First get the max score for normalization
        max_score_body = {
            "query": {
                "bool": {
                    "should": [
                        {"match": {"prompt": q}},
                        {"match": {"query": q}}
                    ],
                    "minimum_should_match": 1
                }
            },
            "size": 1,
            "sort": [{"_score": "desc"}]
        }
        
        max_score_response = es.search(index=INDEX_NAME, body=max_score_body)
        max_score = max_score_response['hits']['hits'][0]['_score'] if max_score_response['hits']['hits'] else 1
        
        # Search in both prompt and query fields with highlighting
        search_body = {
            "query": {
                "bool": {
                    "should": [
                        {"match": {"prompt": q}},
                        {"match": {"query": q}}
                    ],
                    "minimum_should_match": 1
                }
            },
            "highlight": {
                "fields": {
                    "prompt": {},
                    "query": {}
                },
                "pre_tags": ["<em>"],
                "post_tags": ["</em>"]
            },
            "size": size
        }
        
        response = es.search(index=INDEX_NAME, body=search_body)
        
        # Process hits to include both prompt and query with highlights
        hits = []
        for hit in response['hits']['hits']:
            source = hit.get('_source', {})
            highlight = hit.get('highlight', {})
            
            # Calculate match percentage (0-100)
            score = hit.get('_score', 0)
            match_percentage = min(100, int((score / max_score) * 100)) if max_score > 0 else 0
            
            hits.append({
                'prompt': source.get('prompt', ''),
                'query': source.get('query', ''),
                'score': score,
                'match_percentage': match_percentage,
                'highlight': highlight
            })
        
        return {
            'total': response['hits']['total']['value'],
            'hits': hits,
            'took': response['took'],
            'suggestions': []
        }
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Elasticsearch Auto-Suggestions API",
        "version": "1.0.0",
        "endpoints": {
            "search": "/search?q=your_query",
            "autocomplete": "/autocomplete?q=partial_query",
            "health": "/health",
            "indices": "/indices",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
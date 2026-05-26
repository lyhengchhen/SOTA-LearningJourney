from pydantic import Field, BaseModel, HttpUrl
from typing import List, Optional, Literal, Dict
from datetime import datetime

# Search Filter
class DateRange(BaseModel):
    start_date: Optional[datetime] = None 
    end_date: Optional[datetime] = None 
# None = accept either a valid datetime object or None value 

class SearchFilters(BaseModel):
    domain: Optional[List[str]] = None 
    excluded_domain: Optional[List[str]] = None 
    date_range: Optional[DateRange] = None
    safe_search: bool = True
    content: Optional[Literal["web","news","pdf","academic","code"]] = "web" 
    # "Literal" Used to specify that a variable or function argument must be equal to one or more exact, specific values rather than just a general type
    language: Optional[str] = Field(default="en", description= "The {content} could be in any languages.")

# Search Ranking 
class SearchRanking(BaseModel):
    sort_by: Literal["relevance", "date", "popularity"] = "relevance"
    rerank: bool = True
    semantic_search: bool = True
    top_k: int =Field(default=5, ge=1, le=50)

# Agent context 
class AgentContext(BaseModel):
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    memory_enabled: bool = True
    trace_id: Optional[str] = None

# Search Request
class SearchRequest(BaseModel):
    query: str = Field(description= "User's query",
                       min_length= 10,
                       max_length=500)
    filters: Optional[SearchFilters] = None 
    ranking: Optional[SearchRanking] = None 
    agent_context: Optional[AgentContext] = None 

# Citations 
class Citation(BaseModel):
    source_title: str
    source_url: HttpUrl
    snippet: Optional[str] = None

# Search Result Metadata
class ResultMetadata(BaseModel):
    author: Optional[str] = None 
    publication_date: Optional[datetime] = None 
    word_count: Optional[int] = None 
    language: Optional[str] = None 
    score: Optional[float] = Field(default= None, description="Give a score from 0-1")

# Search result 
class SearchResult(BaseModel):
    title: str
    url: HttpUrl
    snippet: str
    metadata: Optional[ResultMetadata] = None
    citation: Optional[List[Citation]] = None 

# Search tracker 
class ExecutionTrace(BaseModel):
    step_name: str
    status: Literal["success", "failed", "running"]
    duration_ms: Optional[int] = None 
    detail: Optional[Dict] = None

# Search response Metadata
class RepsonseMetadata(BaseModel):
    total_result: int
    latency_ms: int
    provider: str
    cached: bool = False
    timestamp: datetime

# Error model 
class ToolError(BaseModel):
    code: str
    error_message: str
    retryable: bool = False

# Finale reponse 
class FinalResponse(BaseModel):
    success: bool 
    query: str
    result: List[SearchResult]
    metadata: ResultMetadata
    execution_trace: Optional[List[ExecutionTrace]] = None
    error: Optional[ToolError] = None








### Basic implementation 
class SearchInput(BaseModel):
    query: str = Field(description="Search query string")
    max_result: int = Field(default=5,
                            ge=1,  #Greater than or equal to
                            le=20, #less than or equal to
                            description="Maximum number of results to return"
                            )

class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str

class SearchOutput(BaseModel):
    results: List[SearchResult]

print("I LOVE YOU")
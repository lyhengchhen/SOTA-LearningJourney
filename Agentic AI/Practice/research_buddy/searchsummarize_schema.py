from pydantic import Field, BaseModel, HttpUrl
from typing import List, Optional, Literal, Dict
from datetime import datetime


# Search Filter
class DateRange(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class SearchFilters(BaseModel):
    domain: Optional[List[str]] = Field(
        default = None,
        description = "Arxiv category filters e.g, ['cs.AI', 'cs.LG', 'quant-ph']"
    )
    excluded_domain: Optional[List[str]] = None
    date_range: Optional[DateRange] = None
    safe_search: bool = True
    content: Optional[Literal["web", "news", "pdf", "academic", "code"]] = "academic"
    language: Optional[str] = Field(
        default="en",
        description="The {content} could be in any languages."
    )


# Search Ranking
class SearchRanking(BaseModel):
    sort_by: Literal["relevance", "date", "popularity"] = Field(
        default="relevance",
        description=(
            "'relevance' = best match to query terms (default for most queries). "
            "'date' = most recently submitted (use for cutting-edge / latest research). "
            "'popularity' = most recently updated (use for actively evolving topics)."
        )
    )
    rerank: bool = Field(
        default=True,
        description=(
            "If True, apply a second-pass reranking after initial retrieval "
            "using semantic similarity to the query. Improves precision at cost of latency."
        )
    )
    semantic_search: bool = Field(
        default=True,
        description="Use semantic/embedding-based search in addition to keyword matching."
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=50,
        description=(
            "Number of papers to return. "
            "5–10 for focused summaries. "
            "20–50 for literature review or broad topic mapping."
        )
    )
    min_relevance_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Filter out results below this relevance threshold after reranking. e.g. 0.6"
    )


# Agent context
class AgentContext(BaseModel):
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    memory_enabled: bool = True
    trace_id: Optional[str] = None


# Search Request   
class SearchRequest(BaseModel):
    query: str = Field(
        description=(
            "The research query to search arXiv. Be specific and use academic terminology. "
            "Good: 'transformer attention mechanism efficiency 2024'. "
            "Bad: 'how does AI work'. "
            "For multi-concept queries, connect with AND/OR."
        ),
        min_length=10,
        max_length=500,
        examples=[
            "Chain of though reasoning in Large Language Model",
            "Diffusion models image generation latent space."
        ]
    )
    filters: Optional[SearchFilters] = None
    ranking: Optional[SearchRanking] = None
    agent_context: Optional[AgentContext] = None


# Citations
class Citation(BaseModel):
    source_title: str = Field(
        description="Full paper title as it appears on arXiv. Do not truncate."
    )
    source_url: HttpUrl = Field(
        description="Canonical arXiv abstract page URL e.g. 'https://arxiv.org/abs/2301.07041'."
    )
    pdf_url: Optional[HttpUrl] = Field(
        default=None,
        description="Direct PDF link e.g. 'https://arxiv.org/pdf/2301.07041'. Separate from abstract URL."
    )
    authors: Optional[List[str]] = Field(
        default=None,
        description="Author list for inline citation formatting e.g. 'chhen et al., 2026'."
    )
    year: Optional[int] = Field(
        default=None,
        description="Publication year. Used in citation formatting."
    )
    arxiv_id: Optional[str] = Field(
        default=None,
        description="Short arXiv ID. Canonical identifier for the paper."
    )
    snippet: Optional[str] = Field(
        default=None,
        description=(
            "The exact sentence(s) from the abstract that support the cited claim. "
            "Max 2 sentences. This is what gets shown inline as evidence."
        )
    )


# Search Result Metadata
class ResultMetadata(BaseModel):
    authors: Optional[List[str]] = Field(
        default=None,
        description="Full list of paper author's in 'Firstname Lastname' format"
    )

    primary_author: Optional[str] = Field(
        default=None,
        description="First/corresponding author. Used for citation formatting e.g. 'Vaswani et al. (2017)'."
    )

    publication_date: Optional[datetime] = Field(
        default=None,
        description="Date first submitted to arXiv. Use for recency filtering and citation."
    )

    last_updated: Optional[datetime] = Field(
        default=None,
        description="Date of most recent revision. A large gap from publication_date signals active revision."
    )

    arxiv_id: Optional[str] = Field(
        default=None,
        description="The short arXiv ID e.g. '2301.07041'. Used to construct PDF and abstract URLs."
    )

    doi: Optional[str] = Field(
        default=None,
        description="DOI if the paper has been published in a journal. None means preprint only."
    )

    categories: Optional[str] = Field(
        default=None,
        description="arXiv category tags e.g. ['cs.LG', 'cs.AI']. Primary category is first in list."
    )

    primary_category: Optional[str] = Field(
        default=None,
        description="The main arXiv category. Tells you the paper's home field at a glance."
    )

    abstract_word_counts: Optional[int] = Field(
        default=None,
        description="Word count of the abstract/snippet. Longer abstracts usually signal more complex papers."
    )

    language: Optional[str] = Field(
        default="en",
        description="ISO 639-1 language code. arXiv is predominantly 'en'."
    )

    relevance_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description=(
            "Relevance score 0.0–1.0 assigned after reranking. "
            "1.0 = perfect match to query. "
            "Use this to sort and filter before passing to summarizer."
        )
    )

    citation_count: Optional[int] = Field(
        default=None,
        description="Number of citations if available. High citation count = high community impact."
    )

    journal_reference: Optional[str] = Field(
        default=None,
        description="Journal reference string if peer-reviewed e.g. 'NeurIPS 2023'. None = preprint."
    )


# Search result
class SearchResult(BaseModel):
    title: str
    url: HttpUrl
    snippet: str
    metadata: Optional[ResultMetadata] = None
    citation: Optional[List[Citation]] = None


# Search tracker
class ExecutionTrace(BaseModel):
    step_name: Literal["arxiv_search", "rerank", "summarize", "pdf_fetch", "cache_lookup"] = Field(
        description="Which pipeline step this trace belongs to."
    )
    status: Literal["success", "failed", "running", "skipped"] = Field(
        description="'skipped' means the step was intentionally bypassed e.g. cache hit."
    )
    duration_ms: Optional[int] = Field(
        default=None,
        description="Wall-clock time for this step. Use to identify bottlenecks."
    )
    input_summary: Optional[str] = Field(
        default=None,
        description="Brief description of what this step received e.g. 'query: transformer attention, top_k: 5'."
    )
    output_summary: Optional[str] = Field(
        default=None,
        description="Brief description of what this step produced e.g. '5 papers retrieved, 3 passed rerank threshold'."
    )
    detail: Optional[Dict] = Field(
        default=None,
        description="Free-form dict for step-specific debug data."
    )


# Search response Metadata
class ResponseMetadata(BaseModel):
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


# Final response
class FinalResponse(BaseModel):
    success: bool
    query: str = Field(description="The original query as submitted.")
    results: List[SearchResult] = Field(
        description="Ranked list of papers, most relevant first."
    )
    summary: Optional[str] = Field(
        default=None,
        description=(
            "LLM-generated synthesis of the results. "
            "Answers the query directly, references papers by [number], "
            "and ends with the most relevant paper recommendation."
        )
    )
    response_metadata: ResponseMetadata = Field(
        description="Request-level metadata: latency, provider, cache status."
    )
    execution_trace: Optional[List[ExecutionTrace]] = Field(
        default=None,
        description="Step-by-step trace of the pipeline. Use for debugging and latency analysis."
    )
    error: Optional[ToolError] = Field(
        default=None,
        description="Populated only when success=False. Contains error code and retry guidance."
    )
 
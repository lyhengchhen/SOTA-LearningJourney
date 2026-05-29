import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from searchsummarize_schema import ToolError, ResponseMetadata, SearchRequest, SearchResult, ResultMetadata, Citation, FinalResponse, ExecutionTrace

"""
Calling the API in Arxiv can be challenging. 
Public API: http://export.arxiv.org/api/{method_name}?{parameters}

For example: https://export.arxiv.org/api/query?search_query=all:transformer&max_results=5
This will return back 'XML' that look like this:
<entry>
  <title>Attention Is All You Need</title>
  <id>https://arxiv.org/abs/1706.03762</id>
  <summary>We propose a new network architecture...</summary>
  <author><name>Ashish Vaswani</name></author>
  <published>2017-06-12T00:00:00Z</published>
</entry>

So it has the title, name of the author, publication id, summary, published date...
"""


"""
The output of this function should look like this at the end
all:transformer AND (cat:cs.AI OR cat:cs.LG) AND ANDNOT cat:econ.GN AND ANDNOT cat:q-fin
"""
def arxiv_query(request: SearchRequest) -> str:
  user_query = f"all{request.query}" # all: tell the arxiv to search the query across all the indexed field (title, abstract, author,...) 
  parted_query = [user_query]
  if request.filters:
    if request.filters.domain:
        concat_clause = " OR ".join(f"(cat:{c})" for c in request.filters.domain)
        parted_query.append({concat_clause})
    if request.filters.excluded_domain:
            parted_query.append(f"ANDNOT cat:{e}" for e in request.filters.excluded_domain)
  return " AND ".join({parted_query})


def sort_order(request: SearchRequest) -> tuple[str, str]:
  ranking = request.ranking 
  sort_by = ranking.sort_by if ranking else "relevance"

  mapping = {"relevance": ("relevance", "descending"),
           "date": ("submittedDate", "descending"),
           "relevance": ("lastUpdateDate", "descending")}

# And our dictionary is storing (sort_field, sort_direction)
# Descending = list newest paper first. Ascending = list oldest paper first.
  return mapping.get(sort_by, ("relevance", "descending"))
# get.(keyname, value)

  # Second method for above function
  # if sort_by == "relevance":
  #     return ("relevance", "descending")
  # elif sort_by == "relevance":
  #     return ("SubmittedDate", "descending")
  # elif sort_by == "lastUpdateDate":
  #     return ("lastUpdatDate", "descending")

import xml.etree.ElementTree as ET 


NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}

def search_entrypoint(entry: ET.Element) -> SearchResult:
    #### ID 
    id_el = entry.find("atom.id", NS)
    raw_id = id_el.text.strip()            # "https://arxiv.org/abs/2201.11903v5"
    arxiv_id = raw_id.split("/abs/")[-1]   # "2201.11903v5"
    arxiv_id = arxiv_id.split("v")[0]      # "2201.119035" Drop the version suffix 
      
    #### Build the URLs using the ID 
    abs_url = f"https://arxiv.org/abs/{arxiv_id}"
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"

    #### Title and abstract extraction 
    title_el = entry.find("atom:title", NS)
    title = title_el.text.strip()
    summary_el = entry.find("atom:summary", NS) 
    snippet = summary_el.text.strip()

    #### Authors extraction 
    authors = []
    for author_el in entry.findall("atom:author", NS):
        name_el = author_el.find("atom:name", NS)
        if name_el is not None:
            authors.append(name_el.text.strip())


    primary_author = authors[0] if authors else None # Present the 1st author as the primary author in case there are multiple contributors 

    #### Extract the data
    public_el = entry.find("atom:published", NS)
    updated_el = entry.find("atom:updated", NS)

    # Normally, the arxiv dates look like "2022-01-28T00:00:00Z"
    # datetime.fromisoformat() can parse this, but needs "Z" --> "+00:00" 
    def parse_date(el):
        if el is None or not el.text:
            return None 
        return datetime.fromisoformat(el.text.replace("Z", "+00:00"))
    
    public_date = public_date(public_el)
    updated_date = updated_date(updated_el)

    #### Extract the categories 
    categories = []
    for cate_el in entry.find("atom:category", NS):
        term = cate_el.get("term") # Read "term" attribute from the tag 
        if term:
            categories.append(term)

    ##### Primary category 
    primary_cate_el = entry.find("atom:primary_category", NS)
    primary_cate = primary_cate_el.get("term") if primary_cate_el is not None else None

    #### Optional fields extraction 
    doi_el = entry.find("atom:doi", NS)
    doi = doi_el.text.strip() if doi_el is not None else None 
    
    journal_el = entry.find("atom:journal", NS)
    journal = journal_el.text.strip() if journal is not None else None 

    #### Build the schema objects 
    metadata = ResultMetadata(
        authors              =       authors,
        primary_author       =       primary_author,
        publication_date     =       public_date,
        last_updated         =       updated_date,
        arxiv_id             =       arxiv_id,
        doi                  =       doi,
        categories           =       ",".join(categories),
        primary_category     =       primary_cate,
        abstract_word_counts =       len(snippet.split),
        language             =       "en",
        relevance_score      =       None,
        journal_reference    =       journal,
    )

    citation = Citation(
        source_title         =       title,
        source_url           =       abs_url,
        pdf_url              =       pdf_url,
        authors              =       authors,
        year                 =       public_date.year if public_date else None,
        arxiv_id             =       arxiv_id,
        snippet              =       snippet[:300]
    )

    return SearchResult(
        title                =       title,
        url                  =       abs_url,
        snippet              =       snippet[:300],
        metadata             =       metadata,
        citation             =       [citation]
    )

import time
import urllib.request

def search_arxiv(request: SearchRequest) -> FinalResponse:
    t0 = time.monotonic()

    # Collect the steps
    traces = []

    ranking = request.ranking
    top_k = ranking.top_k if ranking else 5 
    # Fetch 2 times the top_k so the date filter has room to work 
    # For example, if the top_k = 5, we fetch 10 and trim down after filtering 

    max_result = min(top_k*2, 50)

    sort_by, sort_order = sort_order(request)
    query_str = arxiv_query(request)
     

    # urlib.parse.urlencode safely encodes special characters in the URL 
    # For examle, space become %20, & become %26 

    params = urllib.parse.urlencode({
        "search_query": query_str,
        "start":                0,
        "max_result":  max_result,
        "sortBy":         sort_by,
        "sortOrder":   sort_order,
    })

    url = f"https://export.arxiv.org/api/query?{params}"



    #### Starting the search step
    # tracking  
    traces.append(ExecutionTrace(
        step_name = "arxiv_search",
        status = "running",
        input_summary=f"query={request.query!r}, top_k={top_k}, sort={sort_by},"
    ))

    #### Fetching 
    try: 
        step_t0 = time.monotonic()

        with urllib.request.urlopen(url, timeout=15) as resp: 
            xml_bytes = resp.read()

        fetch_ms = int((time.monotonic() - step_t0) * 1000)

    except Exception as exc: 
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        traces[-1].status = "failed"
        traces[-1].duration_ms = elapsed_ms

        return FinalResponse(
            success = False, 
            query = request.query, 
            results = [],
            execution_trace= traces,
            response_metadata= ResponseMetadata(
                total_result = 0,
                latency_ms = elapsed_ms, 
                provider = "arxiv",
                cached = False, 
                timestamp = datetime.now(timezone.utc)
            ),
            error = ToolError(
                code = "ARXIV_FETCH_ERROR",
                error_message=str(exc),
                retryable=True
            ),
        )
    #### Parse the XML 
    root = ET.fromstring(xml_bytes)
    entries = root.findall("atom:entry", NS)

    results = []
    for entry in entries: 
        try: 
            results.append(search_entrypoint(entry))

        except Exception: 
            continue # Silently skip the malformed entries 
    
    # update the trace 
    traces[-1].status = "success"
    traces[-1].duration_ms = fetch_ms 
    traces[-1].output_summary = f"{len(entries)} fetched, {len(results)} parsed"

    #### Date filter 
    dr = request.filters and request.filters.date_range
    if dr: 
        before = len(results)
        filtered = []
        for r in results:
            pub = r.metadata and r.metadata.publication_date
            if pub:
                if dr.start_date and pub < dr.start_date: 
                    continue
                if dr.end_date and pub > dr.end_date: 
                    continue
            filtered.append(r)
        results = filtered

        traces.append(ExecutionTrace(
            step_name = "arxiv_search",
            status = "sucess",
            output_summary= f"Date filter: {before} -> {len(results)} results",
        ))

    #### Trim to top_k 
    results = results[:top_k]

    #### Return the FinalResponse 
    elapsed_ms = int((time.monotonic() - t0) * 1000)

    return FinalResponse(
        success = True,
        query = request.query, 
        results = results,
        summary = None, # This will be filled in the next ste
        response_metadata= ResponseMetadata(
            total_result = len(results),
            latency_ms= elapsed_ms,
            provider = "arxiv",
            cached = False, 
            timestamp = datetime.now(timezone.utc),
        ), 
        execution_trace= traces, 
        error = None, 
    )
            

print(2+2)
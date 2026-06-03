from searchsummarize_schema import SearchResult, SearchRequest

"""
SearchResult:
- title
- URL (not required for the summarizer)
- Snippet (abstract)
- Metadata (Author)
- Citation
"""

# summarizer.py

from openai import OpenAI

client = OpenAI()

def generate_summary(query, results):
    context = []

    for i, paper in enumerate(results, start=1):
        context.append(
            f"""
Paper [{i}]
Title: {paper.title}

Abstract:
{paper.snippet}
"""
        )


    prompt = f"""
User Question:
{query}

Retrieved Papers:
{''.join(context)}

Summarize the papers and answer the question.
"""
    

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an academic research assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content
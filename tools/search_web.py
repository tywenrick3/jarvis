import os
from tavily import TavilyClient

schema = {
    "name": "search_web",
    "description": (
        "Search the web for a query and return a list of results with titles, "
        "URLs, and short content snippets. Use this to find relevant pages, "
        "then use web_fetch to read specific pages in full."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query",
            }
        },
        "required": ["query"],
    },
}

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY", ""))
    return _client


def execute(query: str) -> str:
    try:
        response = _get_client().search(query, max_results=5)
    except Exception as e:
        return f"Search failed: {e}"

    results = response.get("results", [])
    if not results:
        return "No results found."

    lines = []
    for i, r in enumerate(results, 1):
        title = r.get("title", "No title")
        url = r.get("url", "")
        snippet = r.get("content", "")[:300]
        lines.append(f"{i}. **{title}**\n   {url}\n   {snippet}")

    return "\n\n".join(lines)

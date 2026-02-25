import subprocess

schema = {
    "name": "polymarket_search",
    "description": (
        "Search Polymarket prediction markets by topic. Returns active markets "
        "matching the query with current prices and 24hr changes. Use this after "
        "reading the news to find what markets are pricing on key topics."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Topic to search (e.g. 'Fed rate cut', 'Gavin Newsom')",
            },
            "limit": {
                "type": "integer",
                "description": "Max results (default 5)",
                "default": 5,
            },
        },
        "required": ["query"],
    },
}


def execute(query: str, limit: int = 5) -> str:
    result = subprocess.run(
        ["polymarket", "search", query, "--format", "json", "-n", str(limit)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.stdout.strip() or result.stderr.strip() or "No results."

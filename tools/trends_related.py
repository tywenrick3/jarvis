import subprocess

schema = {
    "name": "trends_related",
    "description": (
        "Get related queries and topics for a search term on Google Trends. Returns top and "
        "rising related searches — useful for understanding what people search alongside a topic "
        "or what breakout subtopics are emerging."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Topic to look up related searches for",
            },
            "geo": {
                "type": "string",
                "description": "Country code (US, GB, DE, JP, etc.) or empty string for worldwide",
                "default": "US",
            },
            "limit": {
                "type": "integer",
                "description": "Max results per category (default 10)",
                "default": 10,
            },
        },
        "required": ["query"],
    },
}


def execute(query: str, geo: str = "US", limit: int = 10) -> str:
    cmd = ["trends", "related", query, "--limit", str(limit), "--format", "json"]
    if geo:
        cmd += ["--geo", geo]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return result.stdout.strip() or result.stderr.strip() or "No results."

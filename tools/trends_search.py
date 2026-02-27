import subprocess

schema = {
    "name": "trends_search",
    "description": (
        "Get Google Trends interest over time for a topic. Returns interest score (0–100), "
        "peak date/value, current value, average, and time series data. Use this to gauge "
        "public interest in a topic — e.g. is 'AI' trending up or down this year?"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Topic to look up (e.g. 'bitcoin', 'artificial intelligence')",
            },
            "timeframe": {
                "type": "string",
                "description": "Time window: 1h, 4h, 1d, 7d, 1m, 3m, 1y, 5y, 10y (default: 1y)",
                "default": "1y",
            },
            "geo": {
                "type": "string",
                "description": "Country code (US, GB, DE, JP, etc.) or empty string for worldwide",
                "default": "US",
            },
        },
        "required": ["query"],
    },
}


def execute(query: str, timeframe: str = "1y", geo: str = "US") -> str:
    cmd = ["trends", "search", query, "--timeframe", timeframe, "--format", "json"]
    if geo:
        cmd += ["--geo", geo]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return result.stdout.strip() or result.stderr.strip() or "No results."

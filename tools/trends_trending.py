import subprocess

schema = {
    "name": "trends_trending",
    "description": (
        "Get today's trending searches on Google Trends. Returns a ranked list of what people "
        "are searching right now. Use this to spot breaking news or viral topics that may not "
        "yet appear in traditional news feeds."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "geo": {
                "type": "string",
                "description": "Country code (US, GB, DE, JP, etc.) — default US",
                "default": "US",
            },
            "limit": {
                "type": "integer",
                "description": "Number of trending topics to return (default 20)",
                "default": 20,
            },
            "realtime": {
                "type": "boolean",
                "description": "Use realtime (last 24h) trends instead of daily. Default false.",
                "default": False,
            },
        },
        "required": [],
    },
}


def execute(geo: str = "US", limit: int = 20, realtime: bool = False) -> str:
    cmd = ["trends", "trending", "--geo", geo, "--limit", str(limit), "--format", "json"]
    if realtime:
        cmd.append("--realtime")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return result.stdout.strip() or result.stderr.strip() or "No results."

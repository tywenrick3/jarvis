import subprocess

schema = {
    "name": "polymarket_movers",
    "description": (
        "Get the top Polymarket prediction markets sorted by 24hr volume. Returns "
        "prices and recent changes. Use as a general pulse check on what markets "
        "are active."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Number of markets (default 5)",
                "default": 5,
            },
        },
        "required": [],
    },
}


def execute(limit: int = 5) -> str:
    result = subprocess.run(
        ["polymarket", "markets", "--format", "json", "-n", str(limit), "--sort", "volume_24hr"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.stdout.strip() or result.stderr.strip() or "No results."

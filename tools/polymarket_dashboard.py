import subprocess

schema = {
    "name": "polymarket_dashboard",
    "description": (
        "Get the Polymarket dashboard — top markets by overall volume. Returns a JSON "
        "list with market titles, current prices, and 24hr changes. Use this to find "
        "one standout market worth highlighting in the briefing."
    ),
    "input_schema": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}


def execute() -> str:
    result = subprocess.run(
        ["polymarket", "dashboard", "--format", "json"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.stdout.strip() or result.stderr.strip() or "No results."

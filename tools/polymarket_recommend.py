import subprocess

schema = {
    "name": "polymarket_recommend",
    "description": (
        "Get the single best Polymarket momentum trade signal. "
        "Uses price movement, volume, and mid-range weighting to surface "
        "the most interesting buy opportunity across top markets."
    ),
    "input_schema": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}


def execute() -> str:
    result = subprocess.run(
        ["polymarket", "recommend", "--format", "json"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.stdout.strip() or result.stderr.strip() or "No recommendation available."

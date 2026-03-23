import subprocess

schema = {
    "name": "polymarket_recommend",
    "description": (
        "Get the best Polymarket trade signal using a chosen strategy. "
        "Strategies: mean-reversion (default, best), momentum, sma, composite, cross-market."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "strategy": {
                "type": "string",
                "description": "Strategy: mean-reversion, momentum, sma, composite, cross-market",
                "default": "mean-reversion",
                "enum": ["mean-reversion", "momentum", "sma", "composite", "cross-market"],
            },
            "top": {
                "type": "integer",
                "description": "Number of signals to surface (default 3)",
                "default": 3,
            },
        },
        "required": [],
    },
}


def execute(strategy: str = "mean-reversion", top: int = 3) -> str:
    result = subprocess.run(
        ["polymarket", "recommend", "-s", strategy, "-n", str(top), "--format", "json"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.stdout.strip() or result.stderr.strip() or "No recommendation available."

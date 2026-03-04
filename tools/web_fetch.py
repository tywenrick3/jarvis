import os
from firecrawl import Firecrawl

MAX_CHARS = 20000

schema = {
    "name": "web_fetch",
    "description": "Fetch the contents of a URL and return the page as clean markdown. Handles JavaScript-rendered pages, paywalls, and anti-bot measures. Response is truncated to ~20k characters.",
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to fetch"
            }
        },
        "required": ["url"]
    }
}

_app = None

def _get_app():
    global _app
    if _app is None:
        _app = Firecrawl(api_key=os.environ.get("FIRECRAWL_API_KEY"))
    return _app


def execute(url: str) -> str:
    try:
        result = _get_app().scrape(url, formats=["markdown"], only_main_content=True)
    except Exception as e:
        return f"Fetch failed for {url}: {e}"

    text = result.markdown or ""

    if not text:
        return f"No content returned for {url}"

    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + f"\n\n... truncated ({len(text)} chars total)"

    return text

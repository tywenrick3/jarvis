import truststore
truststore.inject_into_ssl()

import httpx
import html2text

MAX_CHARS = 20000

schema = {
    "name": "web_fetch",
    "description": "Fetch the contents of a URL and return the response body as markdown. HTML pages are automatically converted to readable markdown. Response is truncated to ~20k characters.",
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

_converter = html2text.HTML2Text()
_converter.ignore_links = False
_converter.ignore_images = True
_converter.body_width = 0

_client = httpx.Client(
    headers={"User-Agent": "Jarvis/1.0"},
    timeout=15,
    follow_redirects=True,
)


def execute(url: str) -> str:
    try:
        resp = _client.get(url)
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        return f"HTTP error {e.response.status_code} fetching {url}"
    except httpx.RequestError as e:
        return f"Request failed for {url}: {e}"

    content_type = resp.headers.get("content-type", "")

    if "html" in content_type:
        text = _converter.handle(resp.text)
    else:
        text = resp.text

    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + f"\n\n... truncated ({len(text)} chars total)"

    return text

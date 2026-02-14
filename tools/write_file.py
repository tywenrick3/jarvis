import os

schema = {
    "name": "write_file",
    "description": "Write content to a file. Creates the file if it doesn't exist, overwrites if it does.",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The file path to write to"
            },
            "content": {
                "type": "string",
                "description": "The content to write"
            }
        },
        "required": ["path", "content"]
    }
}


def execute(path: str, content: str) -> str:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    return f"Wrote {len(content)} bytes to {path}"

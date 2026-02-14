schema = {
    "name": "read_file",
    "description": "Read the contents of a file and return them as a string.",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The file path to read"
            }
        },
        "required": ["path"]
    }
}


def execute(path: str) -> str:
    with open(path, "r") as f:
        return f.read()

import subprocess

schema = {
    "name": "bash",
    "description": "Run a shell command and return its stdout and stderr. Use this to explore the system, run scripts, install packages, etc.",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The bash command to execute"
            }
        },
        "required": ["command"]
    }
}


def execute(command: str) -> str:
    result = subprocess.run(
        command, shell=True, capture_output=True, text=True, timeout=30
    )
    output = ""
    if result.stdout:
        output += result.stdout
    if result.stderr:
        output += f"\nSTDERR:\n{result.stderr}"
    return output.strip() or "(no output)"

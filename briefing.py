import anthropic
import json
from pathlib import Path

from dotenv import load_dotenv
from tools import read_email, read_imessage, search_web, send_imessage

import os

load_dotenv()

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-5-20250929"
SYSTEM_PROMPT_PATH = Path(__file__).parent / "JARVIS.md"
OPERATOR_PHONE = os.environ.get("OPERATOR_PHONE", "")

_modules = [read_email, read_imessage, search_web, send_imessage]
TOOLS = [m.schema for m in _modules]
_registry = {m.schema["name"]: m.execute for m in _modules}


def execute_tool(name: str, input: dict) -> str:
    func = _registry.get(name)
    if func is None:
        return f"Unknown tool: {name}"
    return func(**input)


def load_system_prompt() -> str:
    if SYSTEM_PROMPT_PATH.exists():
        return SYSTEM_PROMPT_PATH.read_text()
    return "You are JARVIS, a sharp and concise personal AI agent."


def run():
    messages = [{"role": "user", "content": "morning briefing"}]
    system = load_system_prompt()
    if OPERATOR_PHONE:
        system += f"\n\nOperator phone number: {OPERATOR_PHONE}"

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=system,
            tools=TOOLS,
            messages=messages,
        )

        for block in response.content:
            if block.type == "text":
                print(block.text)

        if response.stop_reason == "end_turn":
            break

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"  -> {block.name}")
                result = execute_tool(block.name, block.input)
                print(f"  <- {result[:200]}{'...' if len(result) > 200 else ''}\n")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})


if __name__ == "__main__":
    run()

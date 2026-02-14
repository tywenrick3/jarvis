import anthropic
import json
from pathlib import Path

from dotenv import load_dotenv
from tools import TOOLS, execute_tool

load_dotenv()

client = anthropic.Anthropic()
MODEL = "claude-opus-4-6"
SYSTEM_PROMPT_PATH = Path(__file__).parent / "JARVIS.md"


def load_system_prompt() -> str:
    if SYSTEM_PROMPT_PATH.exists():
        return SYSTEM_PROMPT_PATH.read_text()
    return "You are JARVIS, a sharp and concise personal AI agent."


def agent(user_message: str):
    print(f"\n{'='*60}")
    print(f"You: {user_message}")
    print(f"{'='*60}\n")

    messages = [{"role": "user", "content": user_message}]
    system = load_system_prompt()

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
                print(f"Agent: {block.text}")

        if response.stop_reason == "end_turn":
            break

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"  -> tool: {block.name}({json.dumps(block.input, indent=2)})")
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
    import sys

    if len(sys.argv) > 1:
        agent(" ".join(sys.argv[1:]))
    else:
        print("Jarvis 0.0.1(type 'quit' to exit)\n")
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ("quit", "exit", "q"):
                break
            if user_input:
                agent(user_input)

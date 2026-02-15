import json
from pathlib import Path

from dotenv import load_dotenv
from tools import TOOLS, execute_tool
from config import load_config
from models import chat
from usage import UsageTracker

load_dotenv()

cfg = load_config()
tracker = UsageTracker(budget=cfg.budget)
SYSTEM_PROMPT_PATH = Path(__file__).parent / "JARVIS.md"


def load_system_prompt() -> str:
    if SYSTEM_PROMPT_PATH.exists():
        return SYSTEM_PROMPT_PATH.read_text()
    return "You are JARVIS, a sharp and concise personal AI agent."


def agent(user_message: str, messages: list):
    print(f"\n{'='*60}")
    print(f"You: {user_message}")
    print(f"{'='*60}\n")

    messages.append({"role": "user", "content": user_message})
    system = load_system_prompt()

    while True:
        result = chat(cfg.model, system=system, messages=messages, tools=TOOLS)
        tracker.record(result, model_name=cfg.model.name)

        for block in result.content:
            if block.type == "text":
                print(f"Agent: {block.text}")

        if result.stop_reason == "end_turn" or tracker.over_budget:
            break

        tool_results = []
        for block in result.content:
            if block.type == "tool_use":
                print(f"  -> tool: {block.name}({json.dumps(block.input, indent=2)})")
                res = execute_tool(block.name, block.input)
                print(f"  <- {res[:200]}{'...' if len(res) > 200 else ''}\n")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": res,
                })

        messages.append({"role": "assistant", "content": result.content})
        messages.append({"role": "user", "content": tool_results})


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        agent(" ".join(sys.argv[1:]), messages=[])
    else:
        print("Jarvis 0.0.1 (type 'quit' to exit)\n")
        conversation = []
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ("quit", "exit", "q"):
                break
            if user_input:
                agent(user_input, conversation)

    print(f"\n{tracker.summary(cfg.model.name)}")

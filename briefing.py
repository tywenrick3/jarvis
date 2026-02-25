import json
from pathlib import Path

from dotenv import load_dotenv
from tools import read_email, read_imessage, search_web, send_imessage, polymarket_search, polymarket_movers, polymarket_dashboard
from config import load_config
from models import chat
from usage import UsageTracker

import os

load_dotenv()

cfg = load_config()
tracker = UsageTracker(budget=cfg.budget)
SYSTEM_PROMPT_PATH = Path(__file__).parent / "JARVIS.md"
OPERATOR_PHONE = os.environ.get("OPERATOR_PHONE", "")

_modules = [read_email, read_imessage, search_web, send_imessage, polymarket_search, polymarket_movers, polymarket_dashboard]
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
        result = chat(cfg.briefing, system=system, messages=messages, tools=TOOLS)
        tracker.record(result, model_name=cfg.briefing.name)

        for block in result.content:
            if block.type == "text":
                print(block.text)

        if result.stop_reason == "end_turn" or tracker.over_budget:
            break

        tool_results = []
        for block in result.content:
            if block.type == "tool_use":
                print(f"  -> {block.name}")
                res = execute_tool(block.name, block.input)
                print(f"  <- {res[:200]}{'...' if len(res) > 200 else ''}\n")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": res,
                })

        messages.append({"role": "assistant", "content": result.content})
        messages.append({"role": "user", "content": tool_results})

    print(f"\n{tracker.summary(cfg.briefing.name)}")


if __name__ == "__main__":
    run()

from pathlib import Path

from dotenv import load_dotenv
import tools.search_web as search_web
import tools.polymarket_search as polymarket_search
import tools.polymarket_movers as polymarket_movers
import tools.polymarket_recommend as polymarket_recommend
import tools.trends_search as trends_search
import tools.trends_related as trends_related
import tools.check_tennis as check_tennis
import tools.get_weather as get_weather
import tools.send_email as _send_email
from config import load_config
from models import chat
from usage import UsageTracker

import os

load_dotenv()

cfg = load_config()
tracker = UsageTracker(budget=cfg.budget)
SYSTEM_PROMPT_PATH = Path(__file__).parent / "JARVIS_PI.md"
OPERATOR_EMAIL = os.environ.get("OPERATOR_EMAIL", "t_wenrick@apple.com")

_modules = [search_web, polymarket_search, polymarket_movers, polymarket_recommend, trends_search, trends_related, get_weather, check_tennis]
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


def deliver_briefing(text: str):
    from datetime import datetime
    date_str = datetime.now().strftime("%b %-d, %Y")
    result = _send_email.execute(
        to=OPERATOR_EMAIL,
        subject=f"Morning Briefing — {date_str}",
        body=text,
        skip_confirm=True,
    )
    print(f"Delivery: {result}")


def run():
    messages = [{"role": "user", "content": "morning briefing"}]
    system = load_system_prompt()
    briefing_text = []

    while True:
        result = chat(cfg.briefing, system=system, messages=messages, tools=TOOLS)
        tracker.record(result, model_name=cfg.briefing.name)

        for block in result.content:
            if block.type == "text":
                print(block.text)
                briefing_text.append(block.text)

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

    if briefing_text:
        deliver_briefing("\n\n".join(briefing_text))

    print(f"\n{tracker.summary(cfg.briefing.name)}")


if __name__ == "__main__":
    run()

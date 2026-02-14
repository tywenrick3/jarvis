import anthropic
import json

from dotenv import load_dotenv
from tools import TOOLS, execute_tool

load_dotenv()

client = anthropic.Anthropic()
MODEL = "claude-opus-4-6"


def agent(user_message: str):
    print(f"\n{'='*60}")
    print(f"You: {user_message}")
    print(f"{'='*60}\n")

    messages = [{"role": "user", "content": user_message}]
    system = "You are a helpful assistant with access to tools. Use them as needed to accomplish tasks. Work step by step."

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
        print("Jarvis (type 'quit' to exit)\n")
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ("quit", "exit", "q"):
                break
            if user_input:
                agent(user_input)

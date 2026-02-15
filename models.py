"""Provider abstraction — route to Anthropic or OpenAI via a single chat() function."""

from dataclasses import dataclass
from config import ModelConfig

# Cached clients (created once per provider)
_clients: dict = {}


@dataclass
class Usage:
    input_tokens: int
    output_tokens: int


@dataclass
class ChatResult:
    content: list  # Anthropic-style content blocks (text / tool_use dicts)
    stop_reason: str  # "end_turn" or "tool_use"
    usage: Usage


# ---------------------------------------------------------------------------
# Anthropic
# ---------------------------------------------------------------------------

def _get_anthropic():
    if "anthropic" not in _clients:
        import anthropic
        _clients["anthropic"] = anthropic.Anthropic()
    return _clients["anthropic"]


def _chat_anthropic(cfg: ModelConfig, system: str, messages: list, tools: list) -> ChatResult:
    client = _get_anthropic()
    response = client.messages.create(
        model=cfg.name,
        max_tokens=cfg.max_tokens,
        temperature=cfg.temperature,
        system=system,
        tools=tools,
        messages=messages,
    )
    return ChatResult(
        content=response.content,
        stop_reason=response.stop_reason,
        usage=Usage(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        ),
    )


# ---------------------------------------------------------------------------
# OpenAI
# ---------------------------------------------------------------------------

def _get_openai():
    if "openai" not in _clients:
        import openai
        _clients["openai"] = openai.OpenAI()
    return _clients["openai"]


def _convert_tools_to_openai(tools: list) -> list:
    """Convert Anthropic-style tool schemas to OpenAI function-calling format."""
    out = []
    for t in tools:
        out.append({
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": t["input_schema"],
            },
        })
    return out


def _convert_messages_to_openai(system: str, messages: list) -> list:
    """Convert Anthropic messages to OpenAI format.

    Handles:
    - system prompt → {"role": "system"} message
    - assistant content blocks (text/tool_use) → text + tool_calls
    - user tool_result blocks → tool role messages
    """
    oai = [{"role": "system", "content": system}]

    for msg in messages:
        role = msg["role"]
        content = msg["content"]

        if role == "user":
            # Could be a plain string, a list of tool_results, or a list with text
            if isinstance(content, str):
                oai.append({"role": "user", "content": content})
            elif isinstance(content, list):
                # Check if these are tool_result blocks
                if content and isinstance(content[0], dict) and content[0].get("type") == "tool_result":
                    for tr in content:
                        oai.append({
                            "role": "tool",
                            "tool_call_id": tr["tool_use_id"],
                            "content": tr["content"],
                        })
                else:
                    # Generic content blocks — join text
                    text = " ".join(
                        c["text"] if isinstance(c, dict) else str(c) for c in content
                    )
                    oai.append({"role": "user", "content": text})

        elif role == "assistant":
            # content is a list of Anthropic content blocks (TextBlock / ToolUseBlock objects or dicts)
            text_parts = []
            tool_calls = []
            for block in content:
                btype = getattr(block, "type", None) or (block.get("type") if isinstance(block, dict) else None)

                if btype == "text":
                    text_parts.append(getattr(block, "text", None) or block.get("text", ""))
                elif btype == "tool_use":
                    import json
                    name = getattr(block, "name", None) or block.get("name")
                    bid = getattr(block, "id", None) or block.get("id")
                    args = getattr(block, "input", None) or block.get("input", {})
                    tool_calls.append({
                        "id": bid,
                        "type": "function",
                        "function": {
                            "name": name,
                            "arguments": json.dumps(args),
                        },
                    })

            assistant_msg: dict = {"role": "assistant"}
            if text_parts:
                assistant_msg["content"] = "\n".join(text_parts)
            else:
                assistant_msg["content"] = None
            if tool_calls:
                assistant_msg["tool_calls"] = tool_calls
            oai.append(assistant_msg)

    return oai


def _normalize_openai_response(response) -> ChatResult:
    """Convert an OpenAI ChatCompletion into Anthropic-style ChatResult."""
    import json

    choice = response.choices[0]
    msg = choice.message
    content_blocks = []

    if msg.content:
        content_blocks.append(_TextBlock(msg.content))

    if msg.tool_calls:
        for tc in msg.tool_calls:
            content_blocks.append(_ToolUseBlock(
                id=tc.id,
                name=tc.function.name,
                input=json.loads(tc.function.arguments),
            ))

    # Map OpenAI finish_reason to Anthropic stop_reason
    stop_map = {"stop": "end_turn", "tool_calls": "tool_use"}
    stop_reason = stop_map.get(choice.finish_reason, "end_turn")

    return ChatResult(
        content=content_blocks,
        stop_reason=stop_reason,
        usage=Usage(
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
        ),
    )


class _TextBlock:
    """Mimics anthropic TextBlock so the agentic loop can use .type / .text."""
    def __init__(self, text: str):
        self.type = "text"
        self.text = text


class _ToolUseBlock:
    """Mimics anthropic ToolUseBlock so the agentic loop can use .type / .name / .id / .input."""
    def __init__(self, id: str, name: str, input: dict):
        self.type = "tool_use"
        self.id = id
        self.name = name
        self.input = input


def _chat_openai(cfg: ModelConfig, system: str, messages: list, tools: list) -> ChatResult:
    client = _get_openai()
    oai_messages = _convert_messages_to_openai(system, messages)
    oai_tools = _convert_tools_to_openai(tools)

    kwargs = dict(
        model=cfg.name,
        messages=oai_messages,
        tools=oai_tools if oai_tools else None,
        max_completion_tokens=cfg.max_tokens,
        temperature=cfg.temperature,
    )
    # Remove None tools to avoid API error
    if kwargs["tools"] is None:
        del kwargs["tools"]

    response = client.chat.completions.create(**kwargs)
    return _normalize_openai_response(response)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def chat(cfg: ModelConfig, system: str, messages: list, tools: list) -> ChatResult:
    """Send a chat request to the configured provider. Returns a ChatResult."""
    if cfg.provider == "anthropic":
        return _chat_anthropic(cfg, system, messages, tools)
    elif cfg.provider == "openai":
        return _chat_openai(cfg, system, messages, tools)
    else:
        raise ValueError(f"Unknown provider: {cfg.provider}")

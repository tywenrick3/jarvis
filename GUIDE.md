# Personal Agent — Guide & Extension Ideas

## What You Have

An 80-line agentic loop: send messages + tools to Claude, execute tool calls, feed results back, repeat until the model says it's done. Two tools: `bash` and `write_file`.

## Architecture At A Glance

```
User input
    │
    ▼
┌─────────────────────────┐
│  while True:             │
│    response = llm(msgs)  │
│    if done: break        │
│    execute tools          │
│    append results         │
└─────────────────────────┘
    │
    ▼
Final response
```

## Things To Think About As You Extend

### 1. Tools Are Everything

The loop is done. From here, the quality of your agent is determined by the tools you give it. Each tool should:

- Do **one thing** clearly
- Return **concise, useful output** (the model pays per token for tool results too)
- Have a good **description** (this is how the model decides when to use it)
- Handle errors gracefully and return error messages instead of crashing

Tool ideas roughly ordered by usefulness:

| Tool | What it unlocks |
|------|----------------|
| `web_fetch` | Give it access to the internet (use `httpx` or `requests`) |
| `search_web` | Pair with a search API (SerpAPI, Tavily, Brave Search) |
| `sql_query` | Connect it to your database |
| `send_message` | Slack, Discord, email — let it communicate |
| `list_directory` | Structured file exploration |
| `edit_file` | Surgical find-and-replace instead of full file rewrites |

### 2. System Prompt Is Your Steering Wheel

The system prompt is the single biggest lever for controlling behavior. Things to put there:

- **Role and personality**: "You are a sysadmin assistant that speaks concisely"
- **Rules**: "Never delete files without asking", "Always explain before running commands"
- **Context**: working directory, OS, what project you're in
- **Tool guidance**: "Prefer read_file over bash cat"

Keep iterating on it. When the agent does something dumb, the fix is usually in the system prompt.

### 3. Context Window Management

Right now, messages grow forever until you hit the token limit and crash. Solutions from simple to complex:

- **Truncate early messages** — drop the oldest messages when the list gets long
- **Summarize** — periodically ask the model to summarize the conversation so far, replace history with the summary
- **Token counting** — use `anthropic`'s token counting to stay under budget (`client.messages.count_tokens(...)`)
- **Sliding window** — always keep the system prompt + last N messages

This is the first thing that'll bite you in longer sessions.

### 4. Streaming

Right now you wait for the full response. Streaming makes it feel alive:

```python
with client.messages.stream(...) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

Slightly more complex to handle tool calls with streaming, but the Anthropic SDK has examples.

### 5. Persistence & Memory

Your agent forgets everything between runs. Options:

- **Save conversation to a JSON file** — simplest, reload on start
- **Project memory file** — like Claude Code's CLAUDE.md, a file the agent reads at the start of each session
- **Vector store / embeddings** — for searching over large histories (overkill until you need it)

### 6. Multi-Model Strategy

Not every task needs Opus. Consider:

- **Haiku** for simple tool-routing decisions, summarization, quick tasks
- **Sonnet** for most tool-use work
- **Opus** for hard reasoning, planning, complex multi-step tasks

You could even let the agent pick: use a cheap model to classify the task, then route to the right model.

### 7. Safety & Permissions

Right now your agent runs any shell command with no guardrails. Think about:

- **Allowlists/denylists** for commands (no `rm -rf /`, no `sudo`)
- **Confirmation prompts** for destructive actions
- **Sandboxing** — run in Docker so the worst case is a dead container
- **Cost limits** — cap the number of loop iterations or total tokens per session

### 8. Running Autonomously

This is where your agent diverges from Claude Code entirely:

- **Cron jobs** — "every morning, summarize my unread emails"
- **Webhooks** — trigger the agent from GitHub events, Slack messages, etc.
- **File watchers** — react to file changes in a directory
- **Long-running daemon** — keep it alive, listening for events

### 9. Sub-Agents

Once your loop is solid, you can spawn agents from agents:

```python
# Inside a tool, spin up a focused sub-agent
def research_tool(topic: str) -> str:
    return agent(f"Research {topic} and return a 3-bullet summary",
                 model="claude-haiku-4-5-20251001")
```

This is how Claude Code's `Task` tool works — it's agents all the way down.

### 10. Evaluation

As you change things, you'll want to know if your agent is getting better or worse. Simple approach:

- Write 5-10 test prompts with expected outcomes
- Run them after changes
- Check if the agent still does the right thing

No framework needed — a shell script that runs your agent and checks output is fine.

## Useful Libraries

| Library | Purpose |
|---------|---------|
| `anthropic` | Claude API (you have this) |
| `rich` | Pretty terminal output, markdown rendering |
| `httpx` | Async HTTP client for web tools |
| `watchfiles` | File system watcher for autonomous triggers |
| `fastapi` | Webhook receiver if you want to trigger via HTTP |
| `sqlite3` | Dead simple local persistence (built into Python) |

## Resources

- [Anthropic API docs](https://docs.anthropic.com)
- [Tool use guide](https://docs.anthropic.com/en/docs/build-with-claude/tool-use/overview)
- [OpenClaw source](https://github.com/openclaw/openclaw) — reference for a production agent
- [Anthropic cookbook](https://github.com/anthropics/anthropic-cookbook) — practical examples

# JARVIS

Personal AI agent with pluggable tools, multi-provider model abstraction, and automated daily briefings — modeled after a sharp, no-nonsense British butler.

## Project Status

**Active development** — core agentic loop and primary tool suite are operational. Morning briefing runs on a cron schedule. Interactive REPL supports multi-turn conversation with full tool access.

## Architecture

```
User input / cron trigger
        │
        ▼
┌──────────────────────────────┐
│  while True:                 │
│    response = chat(msgs)     │
│    if done: break            │
│    for each tool_use block:  │
│      result = execute(tool)  │
│      append result to msgs   │
└──────────────────────────────┘
        │
        ▼
  Final response
```

Two entry points share this loop:

| Entry Point | Purpose |
|---|---|
| `jarvis.py` | Interactive CLI — REPL or single-command mode |
| `briefing.py` | Automated morning briefing via cron |

Model and provider for each entry point are configured in `config.toml` — swap between Anthropic and OpenAI without touching source code.

System prompt loaded from `JARVIS.md` at runtime. Personality, behavioral rules, tool guidance, and briefing protocol all defined there.

## Model Abstraction

`models.py` exposes a single `chat()` function that normalizes Anthropic and OpenAI into a common `ChatResult` format. The agentic loop is provider-agnostic — tool use, message history, and stop-reason handling work the same regardless of backend.

```toml
# config.toml
[model]
provider = "anthropic"
name     = "claude-opus-4-6"

[model.briefing]
provider = "anthropic"
name     = "claude-sonnet-4-5-20250929"
```

Both providers auto-retry on rate limits (3×, 60 s backoff).

## Tool Suite

Tools live in `tools/`, each exposing a `schema` dict and an `execute` function. They are **explicitly imported** — not auto-discovered. Register a new tool in both `tools/__init__.py` and whichever entry points should use it.

### Communication
| Tool | Method | Notes |
|---|---|---|
| `read_email` | Gmail IMAP | BODY.PEEK (no mark-as-read), MIME decoding, search filters, up to 25 results |
| `send_email` | Gmail SMTP | STARTTLS, optional CC, interactive confirmation before send |
| `read_imessage` | SQLite (`chat.db`) | Direct query against macOS Messages database, handles Cocoa epoch offset |
| `send_imessage` | AppleScript | Via `osascript`, proper escaping, contact name resolution |

### Web
| Tool | Method | Notes |
|---|---|---|
| `search_web` | Tavily API | 5 results max, returns title + URL + snippet |
| `web_fetch` | httpx + html2text | HTML-to-markdown, macOS SSL via truststore, 20k char limit |

### Weather
| Tool | Method | Notes |
|---|---|---|
| `get_weather` | Open-Meteo (free, no key) | Current conditions + 7-day forecast in °F/mph/in; named locations: `home`, `cupertino`, `tahoe`, `all` |

### Markets
| Tool | Method | Notes |
|---|---|---|
| `polymarket_search` | Polymarket CLI | Search prediction markets by keyword |
| `polymarket_movers` | Polymarket CLI | Top movers by volume or price change |
| `polymarket_dashboard` | Polymarket CLI | Portfolio/watchlist overview |

### Trends
| Tool | Method | Notes |
|---|---|---|
| `trends_search` | Google Trends CLI | Interest over time for a query; supports timeframes from 1 h to 10 y |
| `trends_related` | Google Trends CLI | Related queries and topics |
| `trends_trending` | Google Trends CLI | Real-time or daily trending searches |

### System
| Tool | Method | Notes |
|---|---|---|
| `bash` | subprocess | 30 s timeout, captures stdout + stderr |
| `read_file` | Python I/O | Plain file read |
| `write_file` | Python I/O | Creates parent directories, full overwrite |

### Shared Utilities
| Module | Purpose |
|---|---|
| `_contacts.py` | macOS AddressBook lookup — fuzzy name search, phone normalization, reverse lookup |

## Morning Briefing

Runs via `run_briefing.sh` (cron-scheduled). JARVIS compiles and sends an iMessage digest covering:

1. Weather — SF (home), Cupertino (work), Tahoe
2. Unread email summary
3. Recent iMessages needing replies
4. Action items extracted from email and messages
5. Prediction market overview (Polymarket)
6. Google Trends / news signals
7. Top headlines (via web search)

Tool set: `read_email`, `read_imessage`, `search_web`, `send_imessage`, `get_weather`, `polymarket_*`, `trends_*`.

## Configuration

### `config.toml`

Controls provider, model name, max tokens, temperature, and budget thresholds for both entry points. Loaded at startup via `config.py`.

### Environment Variables (`.env`)

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API |
| `OPENAI_API_KEY` | OpenAI API (optional) |
| `TAVILY_API_KEY` | Web search |
| `FIRECRAWL_API_KEY` | Firecrawl web scraping (optional) |
| `EMAIL_ADDRESS` | Gmail address (IMAP/SMTP) |
| `EMAIL_APP_PASSWORD` | Gmail app password |
| `OPERATOR_PHONE` | Phone number for briefing delivery (iMessage) |

Optional: `EMAIL_IMAP_HOST`, `EMAIL_SMTP_HOST`, `EMAIL_SMTP_PORT` (default to Gmail).

## Token Tracking

`usage.py` tracks input/output tokens per session, enforces a configurable budget, and estimates cost using a built-in price table (Anthropic and OpenAI models). Warns at 80% usage and halts the loop when the budget is exceeded.

## Dependencies

| Package | Role |
|---|---|
| `anthropic` | Claude API client |
| `openai` | OpenAI API client (optional) |
| `python-dotenv` | Environment loading |
| `tavily-python` | Web search |
| `httpx` | HTTP client |
| `html2text` | HTML-to-markdown |
| `truststore` | macOS native SSL |

Python 3.11+ required (`tomllib` is stdlib).

## Roadmap

### Near-term
- **Calendar integration** — Read/create events via macOS Calendar. Completes the briefing triad: email + messages + calendar.
- **Conversation persistence** — Save/load conversation history across sessions. JSON file or SQLite.
- **Streaming output** — `client.messages.stream()` for real-time response rendering in the REPL.
- **Reminders tool** — Create Apple Reminders via AppleScript. Natural complement to action-item extraction in briefings.

### Mid-term
- **Context window management** — Token counting, sliding window truncation, periodic summarization to sustain longer sessions.
- **Evening briefing** — Tomorrow's schedule, unanswered messages, next-day weather. Reuses existing cron infrastructure.

### Long-term
- **Sub-agent spawning** — Delegate research and multi-step tasks to focused child agents.
- **Safety and permissions layer** — Bash command allowlists, cost limits, confirmation gates for destructive operations.
- **Webhook and file-watcher triggers** — Respond to external events (GitHub, Slack, filesystem changes).
- **Evaluation framework** — Test prompts with expected outcomes to measure agent quality over time.

## Project Structure

```
jarvis/
├── jarvis.py            # Interactive agent (REPL + single-command)
├── briefing.py          # Automated morning briefing
├── run_briefing.sh      # Cron wrapper for briefing (gitignored)
├── models.py            # Provider abstraction — chat() for Anthropic + OpenAI
├── config.py            # Config loader (dataclasses + tomllib)
├── config.toml          # Model/provider/budget settings
├── usage.py             # Token tracking and cost estimation
├── JARVIS.md            # System prompt — personality, rules, protocols
├── README.md            # This file
├── .env                 # API keys and credentials (not tracked)
├── tools/
│   ├── __init__.py          # Tool registry and dispatcher
│   ├── _contacts.py         # macOS Contacts helper
│   ├── bash.py              # Shell command execution
│   ├── read_file.py         # File reading
│   ├── write_file.py        # File writing
│   ├── read_email.py        # Gmail IMAP reader
│   ├── send_email.py        # Gmail SMTP sender
│   ├── read_imessage.py     # iMessage reader (SQLite)
│   ├── send_imessage.py     # iMessage sender (AppleScript)
│   ├── search_web.py        # Tavily web search
│   ├── web_fetch.py         # URL fetcher + HTML-to-markdown
│   ├── get_weather.py       # Open-Meteo weather (no API key)
│   ├── polymarket_search.py # Prediction market search
│   ├── polymarket_movers.py # Prediction market movers
│   ├── polymarket_dashboard.py # Polymarket portfolio overview
│   ├── trends_search.py     # Google Trends — query interest over time
│   ├── trends_related.py    # Google Trends — related queries
│   └── trends_trending.py   # Google Trends — trending searches
└── venv/                # Python virtual environment
```

## References

- [Anthropic API docs](https://docs.anthropic.com)
- [Tool use guide](https://docs.anthropic.com/en/docs/build-with-claude/tool-use/overview)
- [Anthropic cookbook](https://github.com/anthropics/anthropic-cookbook)

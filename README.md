# JARVIS

A personal AI agent built on Claude, running as a Python CLI. JARVIS handles email, messaging, web research, file operations, and delivers automated daily briefings — modeled after a sharp, no-nonsense British butler.

## Project Status

**Active development** — core agentic loop and primary tool suite are operational. Morning briefing runs on a cron schedule. Interactive REPL supports multi-turn conversation with full tool access.

## Architecture

```
User input / cron trigger
        │
        ▼
┌──────────────────────────────┐
│  while True:                 │
│    response = claude(msgs)   │
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

| Entry Point | Model | Purpose |
|---|---|---|
| `jarvis.py` | Opus 4.6 | Interactive CLI — REPL or single-command mode |
| `briefing.py` | Sonnet 4.5 | Automated morning briefing via cron |

System prompt loaded from `JARVIS.md` at runtime. Personality, behavioral rules, tool guidance, and briefing protocol all defined there.

## Tool Suite

All tools live in `tools/`, each exposing a `schema` and `execute` function. The registry in `tools/__init__.py` collects them automatically.

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

### System
| Tool | Method | Notes |
|---|---|---|
| `bash` | subprocess | 30s timeout, captures stdout + stderr |
| `read_file` | Python I/O | Plain file read |
| `write_file` | Python I/O | Creates parent directories, full overwrite |

### Shared Utilities
| Module | Purpose |
|---|---|
| `_contacts.py` | macOS AddressBook lookup — fuzzy name search, phone normalization, reverse lookup |

## Morning Briefing

Runs via `run_briefing.sh` (cron-scheduled). JARVIS compiles and sends an iMessage digest covering:

1. Weather — SF (home) and South Bay/Cupertino (work)
2. Commute — SF to Cupertino via 280/101
3. Unread email summary
4. Recent iMessages needing replies
5. Action items extracted from email and messages
6. Package delivery status
7. Top 3-5 news headlines (tech/AI/markets)

Uses a reduced tool set (read_email, read_imessage, search_web, send_imessage) on Sonnet 4.5 for cost efficiency.

## Configuration

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API |
| `TAVILY_API_KEY` | Web search |
| `EMAIL_ADDRESS` | Gmail address (IMAP/SMTP) |
| `EMAIL_APP_PASSWORD` | Gmail app password |

Optional: `EMAIL_IMAP_HOST`, `EMAIL_SMTP_HOST`, `EMAIL_SMTP_PORT` (default to Gmail).

## Dependencies

| Package | Role |
|---|---|
| `anthropic` | Claude API client |
| `python-dotenv` | Environment loading |
| `tavily-python` | Web search |
| `httpx` | HTTP client |
| `html2text` | HTML-to-markdown |
| `truststore` | macOS native SSL |

## Roadmap

Ordered by impact and proximity to existing infrastructure.

### Near-term
- **Calendar integration** — Read/create events via macOS Calendar (previously prototyped, source removed). Completes the briefing triad: email + messages + calendar.
- **Conversation persistence** — Save/load conversation history across sessions. JSON file or SQLite.
- **Streaming output** — `client.messages.stream()` for real-time response rendering in the REPL.
- **Reminders tool** — Create Apple Reminders via AppleScript. Natural complement to action-item extraction in briefings.

### Mid-term
- **Context window management** — Token counting, sliding window truncation, periodic summarization to sustain longer sessions.
- **Evening briefing** — Tomorrow's schedule, unanswered messages, next-day weather. Reuses existing cron infrastructure.
- **Multi-model routing** — Classify task complexity, route to Haiku/Sonnet/Opus accordingly.

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
├── run_briefing.sh      # Cron wrapper for briefing
├── JARVIS.md            # System prompt — personality, rules, protocols
├── GUIDE.md             # Developer reference — architecture and extension ideas
├── README.md            # This file
├── .env                 # API keys and credentials (not tracked)
├── tools/
│   ├── __init__.py      # Tool registry and dispatcher
│   ├── _contacts.py     # macOS Contacts helper
│   ├── bash.py          # Shell command execution
│   ├── read_file.py     # File reading
│   ├── write_file.py    # File writing
│   ├── read_email.py    # Gmail IMAP reader
│   ├── send_email.py    # Gmail SMTP sender
│   ├── read_imessage.py # iMessage reader (SQLite)
│   ├── send_imessage.py # iMessage sender (AppleScript)
│   ├── search_web.py    # Tavily web search
│   └── web_fetch.py     # URL fetcher + HTML-to-markdown
└── venv/                # Python 3.13 virtual environment
```

## References

- [Anthropic API docs](https://docs.anthropic.com)
- [Tool use guide](https://docs.anthropic.com/en/docs/build-with-claude/tool-use/overview)
- [Anthropic cookbook](https://github.com/anthropics/anthropic-cookbook)

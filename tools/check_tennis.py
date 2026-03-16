"""Check SF tennis court availability for early morning and evening slots."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, timedelta
from tennis import COURTS, fetch_schedule, parse_slots, fmt_time

schema = {
    "name": "check_tennis",
    "description": "Check SF rec tennis court availability for today. Returns open slots in the early morning (6-8 AM) and evening (after 7 PM) windows across Alice Marble, Lafayette, and Moscone courts.",
    "input_schema": {
        "type": "object",
        "properties": {
            "days": {
                "type": "integer",
                "description": "Number of days to check (default 1 = today only)",
                "default": 1,
            },
        },
        "required": [],
    },
}


def execute(days: int = 1) -> str:
    today = date.today()
    dates = [today + timedelta(days=i) for i in range(days)]

    windows = [
        ("6-8 AM", 6, 8),
        ("After 7 PM", 19, 24),
    ]

    lines = []
    for name, info in COURTS.items():
        court_lines = []
        for day in dates:
            data = fetch_schedule(info["id"], day)
            slots = parse_slots(data, day)

            for label, after, before in windows:
                matched = [s for s in slots if after <= s["start_hour"] < before]
                if matched:
                    day_label = "Today" if day == today else day.strftime("%a %b %-d")
                    for s in matched:
                        start = fmt_time(s["start"])
                        end = fmt_time(s["end"])
                        court_lines.append(
                            f"  {day_label} {start}-{end} ({label}) — {s['court_number']}"
                        )

        if court_lines:
            lines.append(f"{name}:")
            lines.extend(court_lines)

    if not lines:
        return "No tennis courts available in the 6-8 AM or after 7 PM windows."

    return "TENNIS COURTS AVAILABLE\n" + "\n".join(lines)

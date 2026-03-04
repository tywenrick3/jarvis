#!/usr/bin/env python3
"""
Check tennis court availability for the next 7 days across SF rec courts.
Uses the rec.us internal API (no auth required for public courts).

Usage:
    python3 tennis.py                   # show all RESERVABLE slots
    python3 tennis.py --today           # today only
    python3 tennis.py --after 9         # only slots starting at or after 9am
    python3 tennis.py --before 18       # only slots starting before 6pm
    python3 tennis.py --court alice     # filter by court name
"""

import urllib.request
import urllib.error
import json
import shutil
import sys
from datetime import date, timedelta
import argparse

_COLOR = sys.stdout.isatty()

def _c(*codes: int) -> str:
    return f"\033[{';'.join(map(str, codes))}m" if _COLOR else ""

RESET  = _c(0)
BOLD   = _c(1)
DIM    = _c(2)
GREEN  = _c(32)
CYAN   = _c(36)

def bold(s: str) -> str: return f"{BOLD}{s}{RESET}"
def dim(s: str)  -> str: return f"{DIM}{s}{RESET}"
def green(s: str) -> str: return f"{GREEN}{s}{RESET}"
def cyan(s: str)  -> str: return f"{CYAN}{s}{RESET}"

def rule(title: str = "", style: str = "cyan") -> str:
    w = shutil.get_terminal_size((80, 24)).columns
    color = CYAN if style == "cyan" else DIM
    if not title:
        return f"{color}{'─' * w}{RESET}"
    pad = max(0, w - len(title) - 2)
    left = pad // 2
    right = pad - left
    line = "─"
    return f"{color}{line * left} {title} {line * right}{RESET}"

COURTS = {
    "Alice Marble": {
        "id": "81cd2b08-8ea6-40ee-8c89-aeba92506576",
        "slug": "rec.us/alicemarble",
    },
    "Lafayette": {
        "id": "c4fc2b3e-d1bc-47d9-b920-76d00d32b20b",
        "slug": "rec.us/lafayette",
    },
    "Moscone": {
        "id": "fb0d16b1-5f9f-465f-8ebf-fccf5d400c47",
        "slug": "rec.us/moscone",
    },
}

API_BASE = "https://api.rec.us/v1/locations"


def fetch_schedule(location_id: str, day: date) -> dict:
    url = f"{API_BASE}/{location_id}/schedule?startDate={day.strftime('%Y-%m-%d')}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code}: {url}", file=sys.stderr)
        return {}
    except Exception as e:
        print(f"  Error: {e}", file=sys.stderr)
        return {}


def parse_slots(schedule_data: dict, day: date) -> list[dict]:
    day_key = day.strftime("%Y%m%d")
    courts_data = schedule_data.get("dates", {}).get(day_key, [])
    slots = []
    for court in courts_data:
        court_number = court.get("courtNumber", "Court ?")
        for time_range, info in court.get("schedule", {}).items():
            if info.get("referenceType") == "RESERVABLE":
                start_str, end_str = time_range.split(", ")
                start_h, start_m = map(int, start_str.split(":"))
                end_h,   end_m   = map(int, end_str.split(":"))
                duration = (end_h * 60 + end_m) - (start_h * 60 + start_m)
                slots.append({
                    "court_number": court_number,
                    "start": start_str,
                    "end": end_str,
                    "start_hour": start_h + start_m / 60,
                    "duration_min": duration,
                })
    return sorted(slots, key=lambda s: s["start_hour"])


def fmt_time(t: str) -> str:
    h, m = map(int, t.split(":"))
    suffix = "am" if h < 12 else "pm"
    h12 = h % 12 or 12
    return f"{h12}:{m:02d}{suffix}"


def fmt_duration(minutes: int) -> str:
    if minutes < 60:
        return f"{minutes}m"
    h, m = divmod(minutes, 60)
    return f"{h}h {m}m" if m else f"{h}h"


def fmt_slot(s: dict) -> str:
    start = fmt_time(s["start"])
    end   = fmt_time(s["end"])
    dur   = fmt_duration(s["duration_min"])
    court = s["court_number"]
    return f"{green(f'{start} – {end}')}  {dim(dur)}  {dim(court)}"


def check_availability(
    days: int = 7,
    after_hour: float = 0,
    before_hour: float = 24,
    court_filter=None,
) -> None:
    today = date.today()
    dates = [today + timedelta(days=i) for i in range(days)]

    results: dict[str, list[tuple[date, list[dict]]]] = {}

    for name, info in COURTS.items():
        if court_filter and court_filter.lower() not in name.lower():
            continue
        results[name] = []
        for day in dates:
            data  = fetch_schedule(info["id"], day)
            slots = parse_slots(data, day)
            slots = [s for s in slots if after_hour <= s["start_hour"] < before_hour]
            if slots:
                results[name].append((day, slots))

    any_found = any(v for v in results.values())

    date_range = ""
    if days > 1:
        end_day = today + timedelta(days=days - 1)
        date_range = f"  {dim(today.strftime('%b %-d') + ' → ' + end_day.strftime('%b %-d'))}"
    print()
    print(rule(f"{cyan(bold('SF TENNIS'))}{date_range}"))
    print()

    if not any_found:
        print(f"  {dim('No reservable slots found.')}")
        print()
        return

    for name, days_slots in results.items():
        if not days_slots:
            continue

        slug = COURTS[name]["slug"]
        print(f"  {bold(name)}  {dim(slug)}")
        print()

        for day, slots in days_slots:
            is_today = (day == today)
            day_label = "Today" if is_today else day.strftime("%a %b %-d")
            print(f"    {bold(day_label)}")
            for s in slots:
                print(f"      {fmt_slot(s)}")
            print()

    print(rule(style="dim"))
    print()

def main() -> None:
    parser = argparse.ArgumentParser(description="SF tennis court availability")
    parser.add_argument("--today",  action="store_true", help="Check today only")
    parser.add_argument("--days",   type=int, default=7, metavar="N",
                        help="Days to check (default: 7)")
    parser.add_argument("--after",  type=int, default=0,  metavar="HOUR",
                        help="Slots starting at or after this hour (24h)")
    parser.add_argument("--before", type=int, default=24, metavar="HOUR",
                        help="Slots starting before this hour (24h)")
    parser.add_argument("--court",  type=str, default=None,
                        help="Filter: alice | lafayette | moscone")
    args = parser.parse_args()

    check_availability(
        days=1 if args.today else args.days,
        after_hour=args.after,
        before_hour=args.before,
        court_filter=args.court,
    )


if __name__ == "__main__":
    main()

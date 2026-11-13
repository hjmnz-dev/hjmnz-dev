"""Scrape the public contribution calendar (no token, no GraphQL).

Usage: python scripts/fetch_contributions.py
Writes: data/contributions.json
"""
import json
import re
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = "hjmnz-dev"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "contributions.json"


def fetch_days() -> list[dict]:
    url = f"https://github.com/users/{USERNAME}/contributions"
    resp = requests.get(url, headers={"User-Agent": "profile-readme-bot"}, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    counts = {}
    for tip in soup.select("tool-tip[for]"):
        m = re.match(r"\s*(No|[\d,]+) contributions?", tip.get_text())
        if m:
            counts[tip["for"]] = 0 if m.group(1) == "No" else int(m.group(1).replace(",", ""))

    days = []
    for td in soup.select("td.ContributionCalendar-day[data-date]"):
        days.append({
            "date": td["data-date"],
            "level": int(td.get("data-level", 0)),
            "count": counts.get(td.get("id"), 0),
        })
    days.sort(key=lambda d: d["date"])
    if not days:
        raise SystemExit("no contribution cells found; GitHub markup may have changed")
    return days


def stats(days: list[dict]) -> dict:
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] else 0
        longest = max(longest, run)

    # Current streak: today may not have contributions yet, so allow it to be empty.
    current = 0
    rest = days[:-1] if days and days[-1]["count"] == 0 else days
    for d in reversed(rest):
        if not d["count"]:
            break
        current += 1

    best = max(days, key=lambda d: d["count"])
    months = defaultdict(int)
    for d in days:
        months[d["date"][:7]] += d["count"]

    return {
        "total": sum(d["count"] for d in days),
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "active_days": sum(1 for d in days if d["count"]),
        "months": dict(months),
    }


if __name__ == "__main__":
    days = fetch_days()
    payload = {"username": USERNAME, "fetched": date.today().isoformat(), "stats": stats(days), "days": days}
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    s = payload["stats"]
    print(f"{len(days)} days, {s['total']} contributions, streak {s['current_streak']}/{s['longest_streak']}")

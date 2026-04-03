#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import sqlite3
import sys
from typing import Any


def trim(text: str, limit: int = 160) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def iso_ms(value: Any) -> str:
    if not isinstance(value, (int, float)):
        return ""
    try:
        return dt.datetime.fromtimestamp(value / 1000, tz=dt.timezone.utc).isoformat()
    except Exception:
        return ""


def db_path() -> Path:
    return Path.home() / ".local" / "share" / "opencode" / "opencode.db"


def query_rows(sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(sql, params)
        return list(cur.fetchall())
    finally:
        conn.close()


def parse_json(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    return {}


def last_user_prompt(session_id: str) -> str:
    rows = query_rows(
        """
        select p.data as part_data, m.data as message_data
        from message m
        left join part p on p.message_id = m.id
        where m.session_id = ?
        order by m.time_created desc, p.time_created desc
        limit 50
        """,
        (session_id,),
    )
    for row in rows:
        message_data = parse_json(row["message_data"] or "{}")
        if message_data.get("role") != "user":
            continue
        part_data = parse_json(row["part_data"] or "{}")
        text = part_data.get("text")
        if isinstance(text, str) and text.strip():
            return trim(text)
    return ""


def last_assistant_step(session_id: str) -> str:
    rows = query_rows(
        """
        select p.data as part_data, m.data as message_data
        from message m
        left join part p on p.message_id = m.id
        where m.session_id = ?
        order by m.time_created desc, p.time_created desc
        limit 80
        """,
        (session_id,),
    )
    for row in rows:
        message_data = parse_json(row["message_data"] or "{}")
        if message_data.get("role") != "assistant":
            continue
        part_data = parse_json(row["part_data"] or "{}")
        text = part_data.get("text")
        if isinstance(text, str) and text.strip():
            return trim(text)
    return ""


def list_sessions(cwd: Path, limit: int) -> list[dict[str, Any]]:
    rows = query_rows(
        """
        select id, title, directory, time_created, time_updated
        from session
        where directory = ?
        order by time_updated desc
        limit ?
        """,
        (str(cwd), limit),
    )
    items: list[dict[str, Any]] = []
    for row in rows:
        session_id = row["id"]
        items.append(
            {
                "session_id": session_id,
                "title": row["title"],
                "directory": row["directory"],
                "created_at": iso_ms(row["time_created"]),
                "updated_at": iso_ms(row["time_updated"]),
                "last_prompt": last_user_prompt(session_id),
                "last_assistant": last_assistant_step(session_id),
            }
        )
    return items


def build_brief(summary: dict[str, Any]) -> dict[str, Any]:
    latest_prompt = summary.get("last_prompt", "")
    return {
        "session_id": summary["session_id"],
        "title": summary.get("title", ""),
        "goal": latest_prompt or summary.get("title", ""),
        "last_completed_step": summary.get("last_assistant", "") or "No assistant summary found.",
        "last_user_prompt": latest_prompt,
        "likely_next_action": latest_prompt or "Inspect the latest OpenCode transcript before acting.",
        "updated_at": summary.get("updated_at", ""),
    }


def list_command(args: argparse.Namespace) -> int:
    cwd = Path(args.cwd).resolve()
    sessions = list_sessions(cwd, args.limit)
    payload = {"cwd": str(cwd), "count": len(sessions), "sessions": sessions}
    if args.json:
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print(json.dumps(payload, indent=2))
    return 0


def brief_command(args: argparse.Namespace) -> int:
    cwd = Path(args.cwd).resolve()
    sessions = [item for item in list_sessions(cwd, 200) if item["session_id"] == args.session]
    if not sessions:
        print(json.dumps({"error": f"Session not found for this folder: {args.session}", "cwd": str(cwd)}, indent=2), file=sys.stderr)
        return 1
    brief = build_brief(sessions[0])
    if args.json:
        json.dump(brief, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print(json.dumps(brief, indent=2))
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Recover OpenCode session context for the current folder.")
    sub = root.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list")
    p_list.add_argument("--cwd", default=".")
    p_list.add_argument("--limit", type=int, default=5)
    p_list.add_argument("--json", action="store_true")
    p_list.set_defaults(func=list_command)

    p_brief = sub.add_parser("brief")
    p_brief.add_argument("--cwd", default=".")
    p_brief.add_argument("--session", required=True)
    p_brief.add_argument("--json", action="store_true")
    p_brief.set_defaults(func=brief_command)
    return root


def main() -> int:
    args = parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

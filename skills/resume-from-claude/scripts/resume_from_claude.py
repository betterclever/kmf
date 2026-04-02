#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import sys
from typing import Any


def iso_or_blank(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        try:
            return dt.datetime.fromtimestamp(value / 1000, tz=dt.timezone.utc).isoformat()
        except Exception:
            return ""
    if isinstance(value, str):
        return value
    return ""


def trim(text: str, limit: int = 160) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def content_to_text(content: Any, *, include_tool_results: bool = False) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if not isinstance(item, dict):
                continue
            item_type = item.get("type")
            if item_type == "text":
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
            elif include_tool_results and item_type == "tool_result":
                body = item.get("content")
                if isinstance(body, str):
                    parts.append(body)
        return "\n".join(part for part in parts if part).strip()
    return ""


def project_key_for_cwd(cwd: Path) -> str:
    return str(cwd.resolve()).replace("/", "-")


def claude_project_root(cwd: Path) -> Path:
    return Path.home() / ".claude" / "projects" / project_key_for_cwd(cwd)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    if not path.exists():
        return entries
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                entries.append(parsed)
    return entries


def extract_prompt(entry: dict[str, Any], *, include_tool_results: bool = False) -> str:
    message = entry.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        text = content_to_text(content, include_tool_results=include_tool_results)
        if text:
            return trim(text)
    content = entry.get("content")
    if isinstance(content, str):
        return trim(content)
    last_prompt = entry.get("lastPrompt")
    if isinstance(last_prompt, str):
        return trim(last_prompt)
    display = entry.get("display")
    if isinstance(display, str):
        return trim(display)
    return ""


def session_summary(session_path: Path) -> dict[str, Any]:
    entries = load_jsonl(session_path)
    session_id = session_path.stem
    branch = ""
    updated_at = ""
    last_prompt = ""
    last_assistant = ""
    recent_user_prompts: list[str] = []

    for entry in entries:
        branch = entry.get("gitBranch") or branch
        updated_at = iso_or_blank(entry.get("timestamp")) or updated_at

        entry_type = entry.get("type")
        if entry_type == "user":
            prompt = extract_prompt(entry)
            if prompt:
                last_prompt = prompt
                recent_user_prompts.append(prompt)
        elif entry_type == "last-prompt":
            prompt = extract_prompt(entry)
            if prompt:
                last_prompt = prompt
        elif entry_type == "assistant":
            prompt = extract_prompt(entry)
            if prompt and "hit your limit" not in prompt.lower():
                last_assistant = prompt

    return {
        "session_id": session_id,
        "session_file": str(session_path),
        "updated_at": updated_at,
        "branch": branch,
        "last_prompt": last_prompt,
        "last_assistant": last_assistant,
        "recent_user_prompts": recent_user_prompts[-5:],
    }


def find_session_files(project_root: Path) -> list[Path]:
    if not project_root.exists():
        return []
    return sorted(project_root.glob("*.jsonl"))


def sort_summaries(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(items, key=lambda item: item.get("updated_at", ""), reverse=True)


def format_list_text(cwd: Path, summaries: list[dict[str, Any]]) -> str:
    lines = [f"Claude sessions for {cwd}:"]
    for idx, item in enumerate(summaries, start=1):
        branch = item.get("branch") or "(unknown branch)"
        updated_at = item.get("updated_at") or "(unknown time)"
        lines.append(f"{idx}. {item['session_id']} — {updated_at} — {branch}")
        if item.get("last_prompt"):
            lines.append(f"   Last prompt: {item['last_prompt']}")
    if len(lines) == 1:
        lines.append("No Claude sessions found for this folder.")
    return "\n".join(lines)


def build_brief(summary: dict[str, Any]) -> dict[str, Any]:
    recent_prompts = summary.get("recent_user_prompts") or []
    latest_prompt = summary.get("last_prompt", "")
    goal = latest_prompt or (recent_prompts[-1] if recent_prompts else "")
    last_completed = summary.get("last_assistant", "") or "No assistant summary found."
    next_action = latest_prompt or "Inspect the latest transcript tail before acting."
    return {
        "session_id": summary["session_id"],
        "goal": goal,
        "last_completed_step": last_completed,
        "current_branch": summary.get("branch", ""),
        "last_user_prompt": summary.get("last_prompt", ""),
        "likely_next_action": next_action,
        "updated_at": summary.get("updated_at", ""),
        "session_file": summary.get("session_file", ""),
    }


def list_command(args: argparse.Namespace) -> int:
    cwd = Path(args.cwd).resolve()
    project_root = claude_project_root(cwd)
    session_files = find_session_files(project_root)
    summaries = sort_summaries([session_summary(path) for path in session_files])[: args.limit]
    payload = {
        "cwd": str(cwd),
        "project_root": str(project_root),
        "count": len(summaries),
        "sessions": summaries,
    }
    if args.json:
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print(format_list_text(cwd, summaries))
    return 0


def brief_command(args: argparse.Namespace) -> int:
    cwd = Path(args.cwd).resolve()
    project_root = claude_project_root(cwd)
    session_path = project_root / f"{args.session}.jsonl"
    if not session_path.exists():
        print(
            json.dumps(
                {
                    "error": f"Session not found for this folder: {args.session}",
                    "cwd": str(cwd),
                    "project_root": str(project_root),
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1
    summary = session_summary(session_path)
    brief = build_brief(summary)
    if args.json:
        json.dump(brief, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print(f"Session: {brief['session_id']}")
        print(f"Goal: {brief['goal']}")
        print(f"Last completed step: {brief['last_completed_step']}")
        print(f"Branch: {brief['current_branch']}")
        print(f"Likely next action: {brief['likely_next_action']}")
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Recover Claude session context for the current folder.")
    subparsers = root.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List Claude sessions for the current folder")
    list_parser.add_argument("--cwd", default=".", help="Workspace path to match against ~/.claude/projects")
    list_parser.add_argument("--limit", type=int, default=5, help="Maximum number of sessions to print")
    list_parser.add_argument("--json", action="store_true", help="Emit JSON output")
    list_parser.set_defaults(func=list_command)

    brief_parser = subparsers.add_parser("brief", help="Build a short resume brief for a Claude session")
    brief_parser.add_argument("--cwd", default=".", help="Workspace path to match against ~/.claude/projects")
    brief_parser.add_argument("--session", required=True, help="Claude session id")
    brief_parser.add_argument("--json", action="store_true", help="Emit JSON output")
    brief_parser.set_defaults(func=brief_command)

    return root


def main() -> int:
    args = parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

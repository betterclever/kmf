#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


def trim(text: str, limit: int = 160) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def is_meaningful_user_text(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    noise_prefixes = (
        "# AGENTS.md instructions",
        "<permissions instructions>",
        "<collaboration_mode>",
        "<apps_instructions>",
        "<skills_instructions>",
    )
    if stripped.startswith(noise_prefixes):
        return False
    return True


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


def codex_root() -> Path:
    return Path.home() / ".codex"


def extract_text_parts(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        item_type = item.get("type")
        if item_type in {"input_text", "output_text"}:
            text = item.get("text")
            if isinstance(text, str):
                parts.append(text)
    return "\n".join(part for part in parts if part).strip()


def extract_user_text(entry: dict[str, Any]) -> str:
    payload = entry.get("payload")
    if isinstance(payload, dict):
        if entry.get("type") == "response_item" and payload.get("type") == "message" and payload.get("role") == "user":
            return trim(extract_text_parts(payload.get("content")))
        if entry.get("type") == "event_msg":
            event_payload = payload.get("payload")
            if isinstance(event_payload, dict) and payload.get("type") == "user_message":
                message = event_payload.get("message")
                if isinstance(message, str):
                    return trim(message)
    return ""


def extract_assistant_text(entry: dict[str, Any]) -> str:
    payload = entry.get("payload")
    if not isinstance(payload, dict):
        return ""
    if entry.get("type") == "response_item" and payload.get("type") == "message" and payload.get("role") == "assistant":
        return trim(extract_text_parts(payload.get("content")))
    if entry.get("type") == "event_msg":
        event_payload = payload.get("payload")
        if isinstance(event_payload, dict) and payload.get("type") == "agent_message":
            message = event_payload.get("message")
            if isinstance(message, str):
                return trim(message)
    return ""


def session_meta(entry: dict[str, Any]) -> dict[str, Any] | None:
    if entry.get("type") != "session_meta":
        return None
    payload = entry.get("payload")
    if isinstance(payload, dict):
        return payload
    return None


def build_index() -> dict[str, dict[str, Any]]:
    path = codex_root() / "session_index.jsonl"
    result: dict[str, dict[str, Any]] = {}
    for entry in load_jsonl(path):
        session_id = entry.get("id")
        if isinstance(session_id, str):
            result[session_id] = entry
    return result


def iter_session_files() -> list[Path]:
    root = codex_root()
    current = list((root / "sessions").rglob("*.jsonl"))
    archived = list((root / "archived_sessions").glob("*.jsonl"))
    return sorted(current + archived)


def session_summary(session_path: Path, index: dict[str, dict[str, Any]], cwd: Path) -> dict[str, Any] | None:
    entries = load_jsonl(session_path)
    meta: dict[str, Any] | None = None
    last_user_prompt = ""
    last_assistant = ""
    recent_user_prompts: list[str] = []
    updated_at = ""
    branch = ""

    for entry in entries:
        meta = session_meta(entry) or meta
        if meta:
            git_payload = meta.get("git")
            if isinstance(git_payload, dict):
                branch = git_payload.get("branch", "") or branch
            updated_at = meta.get("timestamp", "") or updated_at

        user_text = extract_user_text(entry)
        if user_text and is_meaningful_user_text(user_text):
            last_user_prompt = user_text
            recent_user_prompts.append(user_text)

        assistant_text = extract_assistant_text(entry)
        if assistant_text:
            last_assistant = assistant_text

    if not meta:
        return None

    meta_cwd = meta.get("cwd")
    session_id = meta.get("id")
    if not isinstance(meta_cwd, str) or not isinstance(session_id, str):
        return None
    if Path(meta_cwd).resolve() != cwd:
        return None

    index_entry = index.get(session_id, {})
    thread_name = index_entry.get("thread_name", "") if isinstance(index_entry, dict) else ""
    if not thread_name and recent_user_prompts:
        thread_name = trim(recent_user_prompts[0], limit=80)
    updated_at = index_entry.get("updated_at", updated_at) if isinstance(index_entry, dict) else updated_at

    return {
        "session_id": session_id,
        "session_file": str(session_path),
        "updated_at": updated_at,
        "thread_name": thread_name,
        "branch": branch,
        "last_prompt": last_user_prompt,
        "last_assistant": last_assistant,
        "recent_user_prompts": recent_user_prompts[-5:],
    }


def sort_summaries(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(items, key=lambda item: item.get("updated_at", ""), reverse=True)


def format_list_text(cwd: Path, summaries: list[dict[str, Any]]) -> str:
    lines = [f"Codex sessions for {cwd}:"]
    for idx, item in enumerate(summaries, start=1):
        title = item.get("thread_name") or "(untitled thread)"
        updated_at = item.get("updated_at") or "(unknown time)"
        lines.append(f"{idx}. {item['session_id']} — {updated_at} — {title}")
        if item.get("last_prompt"):
            lines.append(f"   Last prompt: {item['last_prompt']}")
    if len(lines) == 1:
        lines.append("No Codex sessions found for this folder.")
    return "\n".join(lines)


def build_brief(summary: dict[str, Any]) -> dict[str, Any]:
    recent_prompts = summary.get("recent_user_prompts") or []
    latest_prompt = summary.get("last_prompt", "")
    goal = latest_prompt or (recent_prompts[-1] if recent_prompts else "")
    last_completed = summary.get("last_assistant", "") or "No assistant summary found."
    next_action = latest_prompt or "Inspect the latest transcript tail before acting."
    return {
        "session_id": summary["session_id"],
        "thread_name": summary.get("thread_name", ""),
        "goal": goal,
        "last_completed_step": last_completed,
        "current_branch": summary.get("branch", ""),
        "last_user_prompt": latest_prompt,
        "likely_next_action": next_action,
        "updated_at": summary.get("updated_at", ""),
        "session_file": summary.get("session_file", ""),
    }


def list_command(args: argparse.Namespace) -> int:
    cwd = Path(args.cwd).resolve()
    index = build_index()
    summaries = [
        summary
        for path in iter_session_files()
        if (summary := session_summary(path, index, cwd)) is not None
    ]
    summaries = sort_summaries(summaries)[: args.limit]
    payload = {
        "cwd": str(cwd),
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
    index = build_index()
    summaries = [
        summary
        for path in iter_session_files()
        if (summary := session_summary(path, index, cwd)) is not None and summary["session_id"] == args.session
    ]
    if not summaries:
        print(
            json.dumps(
                {
                    "error": f"Session not found for this folder: {args.session}",
                    "cwd": str(cwd),
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1
    brief = build_brief(summaries[0])
    if args.json:
        json.dump(brief, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print(f"Session: {brief['session_id']}")
        print(f"Thread: {brief['thread_name']}")
        print(f"Goal: {brief['goal']}")
        print(f"Last completed step: {brief['last_completed_step']}")
        print(f"Branch: {brief['current_branch']}")
        print(f"Likely next action: {brief['likely_next_action']}")
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Recover Codex session context for the current folder.")
    subparsers = root.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List Codex sessions for the current folder")
    list_parser.add_argument("--cwd", default=".", help="Workspace path to match against Codex session cwd metadata")
    list_parser.add_argument("--limit", type=int, default=5, help="Maximum number of sessions to print")
    list_parser.add_argument("--json", action="store_true", help="Emit JSON output")
    list_parser.set_defaults(func=list_command)

    brief_parser = subparsers.add_parser("brief", help="Build a short resume brief for a Codex session")
    brief_parser.add_argument("--cwd", default=".", help="Workspace path to match against Codex session cwd metadata")
    brief_parser.add_argument("--session", required=True, help="Codex session id")
    brief_parser.add_argument("--json", action="store_true", help="Emit JSON output")
    brief_parser.set_defaults(func=brief_command)

    return root


def main() -> int:
    args = parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

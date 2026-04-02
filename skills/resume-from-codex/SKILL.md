---
name: resume-from-codex
description: Resume a Codex session from Claude, Amp, Droid, OpenCode, and more. Use when the user says `/resume-from-codex`, `/kmf-codex`, asks to resume a Codex conversation here, or wants another agent to recover Codex session state from `~/.codex` and continue the work.
---

# Resume From Codex

Use this skill to recover recent Codex sessions for the current workspace, present a short candidate list, and then continue work from the selected session's recovered state in the current agent.

## When To Use

- The user asks to resume or import a prior Codex conversation.
- The user explicitly says `/kmf-codex` as the shortcut invocation.
- The user gives a Codex session id and wants the current agent to continue it.
- The user wants "the recent Codex chats for this folder" summarized first.

## Workflow

1. Run the bundled script to discover Codex sessions for the current directory:

```bash
python3 scripts/resume_from_codex.py list --cwd "$PWD" --limit 5 --json
```

2. Present a brief numbered list with:
   - session id
   - updated time
   - thread name
   - last user prompt

3. If the user provided a session id, or if there is one clearly relevant latest session, run:

```bash
python3 scripts/resume_from_codex.py brief --cwd "$PWD" --session <session-id> --json
```

4. Use the brief to continue the task. Do not make the user restate context that is already recoverable from the Codex transcript.

## Output Style

When listing sessions, keep it compact:

1. `<session-id>` — `<updated-at>` — `<thread-name>`
2. `Last prompt:` `<summary>`

When resuming a session, give a short import brief:

- Goal
- Last completed step
- Current branch / repo state
- Likely next action

Then continue the work.

## Notes

- Prefer the exact session id if the user supplied one.
- Match sessions by `session_meta.payload.cwd == $PWD`.
- Use `~/.codex/session_index.jsonl` for lightweight metadata and `~/.codex/sessions` / `~/.codex/archived_sessions` for the full transcript.
- The import is a synthesized resume brief, not a byte-for-byte replay of the original chat.
- If the transcript suggests risky or destructive follow-up work, re-check current repo state before acting.

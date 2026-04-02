---
name: resume-from-claude
description: Resume a Claude session from Codex, Amp, Droid, OpenCode, and more. Use when the user says `/resume-from-claude`, `/kmf-claude`, asks to resume a Claude conversation here, or wants another agent to recover Claude session state from `~/.claude` and continue the work.
---

# Resume From Claude

Use this skill to recover recent Claude CLI sessions for the current workspace, present a short candidate list, and then continue work from the selected session's recovered state in the current agent.

## When To Use

- The user asks to resume or import a Claude conversation into Codex.
- The user explicitly says `/kmf-claude` as the shortcut invocation.
- The user gives a Claude session id and wants the current agent to continue it.
- The user wants "the recent Claude chats for this folder" summarized first.

## Workflow

1. Run the bundled script to discover sessions for the current directory:

```bash
python3 scripts/resume_from_claude.py list --cwd "$PWD" --limit 5 --json
```

2. Present a brief numbered list with:
   - session id
   - updated time
   - git branch
   - last prompt

3. If the user provided a session id, or if there is one clearly relevant latest session, run:

```bash
python3 scripts/resume_from_claude.py brief --cwd "$PWD" --session <session-id> --json
```

4. Use the brief to continue the task. Do not make the user restate context that is already recoverable from the Claude transcript.

## Output Style

When listing sessions, keep it compact:

1. `<session-id>` — `<updated-at>` — `<branch>`
2. `Last prompt:` `<summary>`

When resuming a session, give a short import brief:

- Goal
- Last completed step
- Current branch / repo state
- Likely next action

Then continue the work.

## Notes

- Prefer the exact session id if the user supplied one.
- If no project-scoped Claude sessions exist for the current folder, say so directly and stop.
- The import is a synthesized resume brief, not a byte-for-byte replay of the original chat.
- If the transcript suggests risky or destructive follow-up work, re-check current repo state before acting.

---
name: resume-from-opencode
description: Resume an OpenCode session from Codex, Claude, Amp, and more. Use when the user says `/resume-from-opencode`, `/kmf-opencode`, asks to resume an OpenCode conversation here, or wants another agent to recover OpenCode session state and continue the work.
---

# Resume From OpenCode

Use this skill to recover recent OpenCode sessions for the current workspace, present a short candidate list, and then continue work from the selected session's recovered state in the current agent.

## When To Use

- The user asks to resume or import a prior OpenCode conversation.
- The user explicitly says `/kmf-opencode` as the shortcut invocation.
- The user gives an OpenCode session id and wants the current agent to continue it.
- The user wants "the recent OpenCode chats for this folder" summarized first.

## Workflow

1. Run the bundled script to discover OpenCode sessions for the current directory:

```bash
python3 scripts/resume_from_opencode.py list --cwd "$PWD" --limit 5 --json
```

2. Present a brief numbered list with:
   - session id
   - updated time
   - title
   - last user prompt

3. If the user provided a session id, or if there is one clearly relevant latest session, run:

```bash
python3 scripts/resume_from_opencode.py brief --cwd "$PWD" --session <session-id> --json
```

4. Use the brief to continue the task. Do not make the user restate context that is already recoverable from the OpenCode transcript.

## Notes

- Prefer the exact session id if the user supplied one.
- Match sessions by `directory == $PWD`.
- Read session metadata from the OpenCode sqlite store, then derive user/assistant summaries from recent message and part rows.
- The import is a synthesized resume brief, not a byte-for-byte replay of the original chat.

> *As Kid Cudi and Kanye say on "Reborn": "keep movin' forward, keep movin' forward."*

# kmf

The work should not stop when your limits run out.

This repo is about persistence: recovering context, resuming work, and carrying momentum across tools, sessions, and agents without making the user start over. The first skill starts with Claude session recovery, but the bigger idea is simple: the work never resets just because the agent changed.

## Install

```bash
npx skills add betterclever/kmf --skill resume-from-claude -y --full-depth
npx skills add betterclever/kmf --skill resume-from-codex -y --full-depth
```

To inspect available skills first:

```bash
npx skills add betterclever/kmf -l --full-depth
```

## Skills

- `resume-from-claude` — recover Claude CLI sessions for the current folder, present a short candidate list, and build a resume brief Codex can continue from
- `resume-from-codex` — recover Codex sessions for the current folder, present a short candidate list, and build a resume brief another Codex session can continue from

## Planned

- `resume-from-droid`
- `resume-from-xyz`

## Repo-local validation

```bash
npx skills add betterclever/kmf -l --full-depth
python3 skills/resume-from-claude/scripts/resume_from_claude.py list --cwd "$PWD" --limit 5 --json
python3 skills/resume-from-codex/scripts/resume_from_codex.py list --cwd "$PWD" --limit 5 --json
```

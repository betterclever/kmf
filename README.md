Inspired by "Reborn" by Kid Cudi and Kanye West, this repo is about one thing: keep moving forward.

# kmf

A small collection of persistence-oriented agent skills that help one agent recover context from another and continue the work without making the user restate everything.

## Install

```bash
npx skills add betterclever/kmf --skill resume-from-claude -y --full-depth
```

To inspect available skills first:

```bash
npx skills add betterclever/kmf -l --full-depth
```

## Skills

- `resume-from-claude` — recover Claude CLI sessions for the current folder, present a short candidate list, and build a resume brief Codex can continue from

## Planned

- `resume-from-codex`
- `resume-from-droid`
- `resume-from-xyz`

## Repo-local validation

```bash
npx skills add betterclever/kmf -l --full-depth
python3 skills/resume-from-claude/scripts/resume_from_claude.py list --cwd "$PWD" --limit 5 --json
```

> *As Kid Cudi and Kanye say on "Reborn": "keep movin' forward, keep movin' forward."*

# kmf

The work should not stop when your limits run out.

kmf helps the next agent continue the work instead of starting over.

## Install

```bash
npx skills add betterclever/kmf --skill resume-from-claude -y --full-depth
npx skills add betterclever/kmf --skill resume-from-codex -y --full-depth
npx skills add betterclever/kmf --skill resume-from-opencode -y --full-depth
```

To inspect available skills first:

```bash
npx skills add betterclever/kmf -l --full-depth
```

## Skills

- `resume-from-claude` — resume a Claude session from Codex, Amp, OpenCode, and more
- `resume-from-codex` — resume a Codex session from Claude, Amp, OpenCode, and more
- `resume-from-opencode` — resume an OpenCode session from Codex, Claude, Amp, and more

## How it works

1. kmf finds prior sessions for the current folder.
2. It pulls the important context into a short resume brief.
3. The next agent picks up the thread instead of making you start over.

## Planned

- `resume-from-droid`
- `resume-from-xyz`

## Repo-local validation

```bash
npx skills add betterclever/kmf -l --full-depth
python3 skills/resume-from-claude/scripts/resume_from_claude.py list --cwd "$PWD" --limit 5 --json
python3 skills/resume-from-codex/scripts/resume_from_codex.py list --cwd "$PWD" --limit 5 --json
python3 skills/resume-from-opencode/scripts/resume_from_opencode.py list --cwd "$PWD" --limit 5 --json
```

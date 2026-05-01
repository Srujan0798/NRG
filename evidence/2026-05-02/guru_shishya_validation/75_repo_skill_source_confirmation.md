# Repo Skill Source Confirmation

Date: 2026-05-02

Founder correction: for NRG work, use only the skills stored in the repository
so the workflow survives cloning to another machine.

## Confirmed Source

Authoritative paths:

- `.claude/skills`
- `.agents/skills`

Non-authoritative for this project:

- `$CODEX_HOME/skills`
- user-home plugin caches
- any external/global skill inventory

## Counts

| Repo path | Directory count | Skill file count | Note |
| --- | ---: | ---: | --- |
| `.claude/skills` | 86 | 86 `SKILL.md` | Guru/Claude protocols |
| `.agents/skills` | 51 | 50 `SKILL.md` + 1 `SKILL.MD` | Shishya execution skills |
| Total | 137 | 137 | Clone-portable repo skill directories |

Shared skill names between `.claude/skills` and `.agents/skills`: only
`nrg-validation-campaign`.

## Operational Rule

When an NRG task mentions skills, default to repo-contained skills only. If a
skill exists in user-home/global context but not in this repository, do not treat
it as part of the NRG project workflow unless the Founder explicitly asks for
that external skill.

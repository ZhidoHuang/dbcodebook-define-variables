# dbCodeBook Variable Definition Skill

A portable Codex Skill for defining, revising, auditing, and validating variables from longitudinal databases supported by dbCodeBook.

Current database workflows:

- CHARLS
- ELSA

## What It Contains

- stable definition workflows and database profiles
- reader-facing writing and Criteria rules
- task-card and profile templates
- environment, source-record, output, and R-run checks
- localhost dbCodeBook export recovery support

Raw data, formal topic outputs, mutable indexes, logs, credentials, and topic-specific adjudications are intentionally excluded.

## Setup

1. Place the repository in a Codex Skills directory.
2. Configure `DBCODEBOOK_HOME`.
3. Configure optional external paths when needed:
   - `DBCODEBOOK_R_PACKAGE_ROOT`
   - `DBCODEBOOK_BOOKAPP_ROOT`
   - `DBCODEBOOK_RSCRIPT`
   - `DBCODEBOOK_PYTHON`
4. Run:

```powershell
.\scripts\check_environment.ps1
```

Read [SKILL.md](SKILL.md) for task behavior and [the migration guide](references/migration-guide.md) for cross-computer setup.

## Repository Boundary

This repository contains reusable workflow code and documentation only. Never commit survey microdata, exported raw files, credentials, personal information, formal research outputs, or local environment values.


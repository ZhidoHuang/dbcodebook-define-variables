# Migration Guide

This Skill stores stable workflow rules, templates, and deterministic checks. It does not store raw data, formal topic outputs, mutable indexes, logs, or topic-specific adjudications.

## Move to Another Computer

1. Copy or clone the whole `dbcodebook-define-variables` directory.
2. Keep the definition workspace and source repositories outside the Skill.
3. Configure:
   - `DBCODEBOOK_HOME`
   - `DBCODEBOOK_R_PACKAGE_ROOT` when the package is not under `<DBCODEBOOK_HOME>\R package\dbCodeBookr`
   - `DBCODEBOOK_BOOKAPP_ROOT` when local export recovery is required
   - `DBCODEBOOK_RSCRIPT` when `Rscript` is not on `PATH`
   - `DBCODEBOOK_PYTHON` when `py` or `python` is not on `PATH`
4. Run `scripts\check_environment.ps1`.
5. Install or link the Skill only after the environment report returns `ok: true`.

For the bundled R tests on Windows, set `DBCODEBOOK_SKILL_ROOT` to the Skill directory before running `scripts\tests\test_summary_fact_helpers.R`. This avoids locale-dependent command-line decoding when the Skill path contains non-ASCII characters.

## Activation Boundary

- Keep the candidate outside the active Codex Skill directory while comparing behavior.
- Do not delete or disable the current thin Skills during candidate validation.
- Activate the candidate only after explicit user approval.
- After activation, treat this Skill as the stable definition rule source. Keep legacy workspace rule directories read-only until a separate cleanup decision.

## Version Control

Use a Git repository to transport and version the Skill. A public repository is appropriate only after a secret and privacy scan confirms that it contains reusable workflow code and documentation only. Keep raw data, formal outputs, credentials, mutable indexes, topic-specific evidence, and local environment values outside the repository.

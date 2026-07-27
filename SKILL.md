---
name: dbcodebook-define-variables
description: Define, revise, audit, or validate variables for dbCodeBook-supported longitudinal databases such as CHARLS and ELSA. Use for database-topic discovery, candidate-variable review, literature-grounded definition decisions, formal R generation, Criteria and note generation, source recovery, machine checks, or deciding whether validated definition changes require a separate promotional refresh.
---

# dbCodeBook Variable Definition

Use this Skill as the portable source of stable definition rules, templates, and deterministic checks. Keep raw data, mutable indexes, formal outputs, logs, and topic-specific adjudications in the configured workspace.

## Resolve the Workspace

Read `DBCODEBOOK_HOME` from the environment. Accept an explicit user-provided root when the variable is absent. Derive:

- definition root: `<DBCODEBOOK_HOME>/演示/定义`
- R package root: `<DBCODEBOOK_HOME>/R package/dbCodeBookr`, unless `DBCODEBOOK_R_PACKAGE_ROOT` is set
- bookapp root: `DBCODEBOOK_BOOKAPP_ROOT`
- Rscript: `DBCODEBOOK_RSCRIPT` or the first `Rscript` available on `PATH`
- Python: `DBCODEBOOK_PYTHON` or the first `py`/`python` available on `PATH`

Before an actionable task on a new computer, run:

```powershell
<skill-root>\scripts\check_environment.ps1
```

Do not write files when the environment check fails.
For transfer and activation steps, read [migration-guide.md](references/migration-guide.md).

## Load Rules Progressively

For every actionable task, read:

1. [project-governance.md](references/project-governance.md)
2. [directory-structure.md](references/directory-structure.md)
3. [user-material-rules.md](references/user-material-rules.md)
4. [validation-rules.md](references/validation-rules.md)

Then read only the selected database branch:

- CHARLS: [charls-workflow.md](references/charls-workflow.md) and [charls-profile.md](references/charls-profile.md)
- ELSA: [elsa-workflow.md](references/elsa-workflow.md) and [elsa-profile.md](references/elsa-profile.md)

Read mutable workspace files only when they exist and the task needs them:

- `<definition-root>/_索引/主题索引.md`
- `<definition-root>/_索引/定义验收台账.md`
- the selected topic's current formal R, raw files, and user materials

Apply this precedence:

1. the user's latest explicit decision;
2. project governance and directory boundaries;
3. the selected database workflow;
4. common user-material rules;
5. validated topic-specific facts;
6. the database profile as search and risk guidance.

Do not infer a public rule from one completed topic.

## Classify the Request

- **Discussion or rule review:** explain and draft; do not modify formal files.
- **New definition:** complete discovery and evidence gates before formal generation.
- **Revision:** identify whether the requested change affects facts, business logic, wording, layout, or only downstream promotion.
- **Audit:** remain read-only unless the user explicitly asks for correction.
- **Promotion:** report which user-facing surfaces changed and hand off to the relevant promotion Skill; do not edit promotion assets here.

## Execute the Definition Workflow

1. Confirm database, topic, intended concepts, and output scope.
2. Perform real dbCodeBook discovery through actual keyword search or real directory entry; record the exact route used.
3. Conduct literature review when construct choice, scoring, comparability, or interpretation requires external evidence.
4. Build a candidate inventory from actual database evidence. Do not reverse-engineer candidates from an old finished definition.
5. Present unresolved research or mapping decisions to the user before formal execution.
6. Recover or prepare approved raw inputs without silently replacing existing formal raw files.
7. Draft Criteria and note prose from formal business code, raw values, raw codebook labels, literature evidence, and explicit adjudications. Old prose may be used only after the first draft for omission checks.
8. Generate formal R, workbooks, QA, definition HTML, detail HTML, and the note from the formal source.
9. Run focused machine checks proportional to the change. Do not add a second validation task unless [validation-rules.md](references/validation-rules.md) requires it.
10. Report exact outputs, changed user-facing surfaces, unresolved risks, and whether promotion needs a separate refresh.

## Protect Content Quality

- Write for ordinary readers with concise, natural statements.
- Describe the actual decision logic, not implementation syntax.
- State ordinary missingness only when it changes interpretation or a downstream result.
- For formulas, present the result formula before explaining component conversions.
- For continuous variables, the classification line contains the variable type and unit.
- Put same-meaning name changes in definition logic when they explain which source is read.
- Put same-name meaning changes in notes when they affect interpretation.
- Omit an empty notes section instead of writing `无`, `暂无`, or `不适用`.
- Do not govern prose through word blacklists or sentence-difference metrics.

## Use Bundled Resources

Scripts:

- `scripts/recover_bookapp_export.py`: recover a previously created local bookapp export.
- `scripts/run_r_definition.ps1`: execute a formal R definition with public-code boundary checks.
- `scripts/check_definition_output.py`: validate generated definition outputs.
- `scripts/check_definition_source_record.py`: validate source-retrieval evidence.
- `scripts/render_definition_bundle.R`: render definition materials.
- `scripts/summary_fact_helpers.R`: derive summary facts from formal outputs.

Templates:

- `assets/definition-task-card-template.md`
- `assets/current-task-template.md`
- `assets/database-profile-template.md`
- `assets/qa-safe-summary.R`
- `assets/retrieval-record-template.json`

Treat the bundled copies as the candidate Skill's only stable rule source. Do not read the legacy `_流程`, `_模板`, `_工具`, or old thin Skills after this Skill is formally activated.

## Close Safely

- Never overwrite raw files, formal outputs, or mutable indexes merely to test the Skill.
- Keep experimental files outside formal topic directories.
- Preserve one successful formal log when the selected workflow requires a formal run.
- Report `MACHINE_CHECK_PASS` only when required checks actually pass.
- Do not claim user acceptance.
- Do not update promotional assets automatically.

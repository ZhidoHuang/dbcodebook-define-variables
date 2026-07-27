"""Recover a localhost bookapp export from an AssetTransaction record.

Run with the bookapp virtualenv Python, for example:

    python recover_bookapp_export.py \
        --bookapp-root <BOOKAPP_ROOT> \
        --db charls \
        --transaction <TRANSACTION_ID> \
        --out <OUTPUT_DIRECTORY> \
        --expect-vars <COMMA_SEPARATED_VARIABLES>

Or skip the profile/downloads page and recover the newest matching transaction:

    python recover_bookapp_export.py \
        --bookapp-root <BOOKAPP_ROOT> \
        --db charls \
        --latest \
        --out <OUTPUT_DIRECTORY> \
        --expect-vars <COMMA_SEPARATED_VARIABLES>

This tool is for localhost bookapp recovery after the page workflow has already
selected variables, previewed data, clicked download, and created a download
record. It does not replace the page workflow.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Iterable


BOOKAPP_ROOT: Path | None = None
REQUIRED_ZIP_MEMBERS = {"raw_data.csv", "raw_codebook.csv"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Recover raw_data/raw_codebook from a localhost bookapp transaction."
    )
    parser.add_argument("--db", required=True, help="Expected bookapp source, e.g. charls.")
    parser.add_argument(
        "--bookapp-root",
        type=Path,
        default=None,
        help="Local bookapp repository root. Defaults to DBCODEBOOK_BOOKAPP_ROOT.",
    )
    parser.add_argument(
        "--transaction",
        required=False,
        type=int,
        help="AssetTransaction id shown in the bookapp downloads record.",
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Use the newest AssetTransaction matching --db and --expect-vars.",
    )
    parser.add_argument(
        "--latest-limit",
        type=int,
        default=50,
        help="How many recent transactions to scan when --latest is used.",
    )
    parser.add_argument(
        "--out",
        required=True,
        type=Path,
        help="Output directory for bookapp_download.zip, raw_data.csv, and raw_codebook.csv.",
    )
    parser.add_argument(
        "--expect-vars",
        required=True,
        help="Comma-separated expected variable names in the exact page selection order.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting existing recovered files in the output directory.",
    )
    return parser.parse_args()


def fail(message: str, *, detail: object | None = None) -> None:
    payload = {"ok": False, "error": message}
    if detail is not None:
        payload["detail"] = detail
    print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
    raise SystemExit(1)


def normalize_var_name(value: str) -> str:
    return value.split(" (", 1)[0].strip()


def parse_expected_vars(raw: str) -> list[str]:
    values = [item.strip() for item in raw.split(",") if item.strip()]
    if not values:
        fail("--expect-vars is empty.")
    duplicates = sorted({item for item in values if values.count(item) > 1})
    if duplicates:
        fail("--expect-vars contains duplicated variables.", detail=duplicates)
    return values


def ensure_bookapp_venv() -> None:
    assert BOOKAPP_ROOT is not None
    exe = Path(sys.executable).resolve()
    expected = BOOKAPP_ROOT / "venv"
    try:
        exe.relative_to(expected)
    except ValueError:
        fail(
            "Use bookapp's virtualenv Python, not system Python.",
            detail={
                "sys_executable": str(exe),
                "expected_prefix": str(expected),
            },
        )


def prepare_output_dir(out_dir: Path, overwrite: bool) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    managed = [
        out_dir / "bookapp_download.zip",
        out_dir / "raw_data.csv",
        out_dir / "raw_codebook.csv",
        out_dir / "recover_bookapp_export_QA.txt",
    ]
    existing = [str(path) for path in managed if path.exists()]
    if existing and not overwrite:
        fail(
            "Output files already exist. Pass --overwrite only when this is an intentional tool test or rerun.",
            detail=existing,
        )


def setup_django(temp_media_root: Path) -> None:
    assert BOOKAPP_ROOT is not None
    # The bookapp settings and CHARLS views still contain POSIX-style paths
    # such as /app/database. On Windows those paths resolve against the
    # current drive, so force the process onto D: before django imports.
    os.chdir(BOOKAPP_ROOT)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bookapp.settings")
    sys.path.insert(0, str(BOOKAPP_ROOT))

    import django
    from django.conf import settings

    django.setup()
    settings.MEDIA_ROOT = str(temp_media_root)


def get_transaction(transaction_id: int):
    from assets.models import AssetTransaction

    try:
        return AssetTransaction.objects.get(id=transaction_id)
    except AssetTransaction.DoesNotExist:
        fail("AssetTransaction not found.", detail={"transaction": transaction_id})


def transaction_vars(transaction) -> list[str]:
    variables = transaction.variables or []
    return [
        var.get("label") or normalize_var_name(var.get("name", ""))
        for var in variables
    ]


def get_latest_matching_transaction(expected_db: str, expected_vars: list[str], limit: int):
    from assets.models import AssetTransaction

    candidates = AssetTransaction.objects.order_by("-id")[:limit]
    matches = []
    inspected = []
    for transaction in candidates:
        variables = transaction.variables or []
        if not variables:
            inspected.append(
                {
                    "id": transaction.id,
                    "source": "",
                    "vars": [],
                }
            )
            continue
        source = (variables[0].get("source") or "").strip().lower()
        vars_ = transaction_vars(transaction)
        inspected.append(
            {
                "id": transaction.id,
                "source": source,
                "vars": vars_,
            }
        )
        if source == expected_db and vars_ == expected_vars:
            matches.append(transaction)

    if not matches:
        fail(
            "No recent transaction matches --db and --expect-vars exactly.",
            detail={
                "expected_db": expected_db,
                "expected_vars": expected_vars,
                "latest_limit": limit,
                "recent_transactions": inspected[:10],
            },
        )
    if len(matches) > 1:
        # Pick newest deterministically, but report that older matching records exist.
        newest = matches[0]
        newest._matching_transaction_ids = [item.id for item in matches]  # type: ignore[attr-defined]
        return newest
    matches[0]._matching_transaction_ids = [matches[0].id]  # type: ignore[attr-defined]
    return matches[0]


def transaction_source(transaction) -> str:
    variables = transaction.variables or []
    if not variables:
        fail("Transaction has no variables.", detail={"transaction": transaction.id})
    return (variables[0].get("source") or "").strip().lower()


def build_columns(source: str, variables: list[dict]) -> list[dict]:
    if source in {"elsa", "creles"}:
        columns = []
        for var in variables:
            original = var["name"]
            rename = var.get("label", "")
            if " (" in original and original.endswith(")"):
                variable = original[: original.rfind(" (")]
                file_name = original[original.rfind(" (") + 2 : -1]
            else:
                variable = original
                file_name = ""
            columns.append(
                {
                    "original": original,
                    "rename": rename,
                    "variable": variable,
                    "file": file_name,
                }
            )
        return columns

    if source == "nhanes":
        columns = []
        for var in variables:
            name = var["name"]
            rename = var.get("label", "")
            if " (" in name and name.endswith(")"):
                variable = name[: name.rfind(" (")]
                source_type = name[name.rfind(" (") + 2 : -1]
            else:
                variable = name
                source_type = ""
            columns.append(
                {
                    "original": variable,
                    "rename": rename,
                    "variable": variable,
                    "sourceType": source_type,
                }
            )
        return columns

    return [
        {
            "original": var["name"],
            "rename": var.get("label", ""),
        }
        for var in variables
    ]


def export_response(source: str, transaction, columns: list[dict]):
    from django.test import RequestFactory

    request = RequestFactory().post(f"/home/{source}/export/")
    request.user = transaction.user

    if source == "charls":
        from data.views.charls_views import export_charls_data

        return export_charls_data(request, redownload_data={"columns": columns})
    if source == "elsa":
        from data.views.elsa_views import export_elsa_data

        return export_elsa_data(request, redownload_data={"columns": columns})
    if source == "creles":
        from data.views.creles_views import export_creles_data

        return export_creles_data(request, redownload_data={"columns": columns})
    if source == "nhanes":
        from data.views.data_views import export_data

        return export_data(request, redownload_data={"columns": columns})

    fail(
        "Unsupported db/source for this recovery tool.",
        detail={
            "source": source,
            "supported": ["charls", "elsa", "creles", "nhanes"],
        },
    )


def decode_body(response, limit: int = 1000) -> str:
    return getattr(response, "content", b"").decode("utf-8", errors="replace")[:limit]


def write_zip_and_extract(response, out_dir: Path) -> list[str]:
    status_code = getattr(response, "status_code", None)
    if status_code != 200:
        fail(
            "bookapp export failed.",
            detail={"status_code": status_code, "body": decode_body(response)},
        )

    content_type = response.get("Content-Type", "")
    if "application/zip" not in content_type:
        fail(
            "bookapp export did not return a zip response.",
            detail={"content_type": content_type, "body": decode_body(response)},
        )

    zip_path = out_dir / "bookapp_download.zip"
    zip_path.write_bytes(response.content)

    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        missing = sorted(REQUIRED_ZIP_MEMBERS.difference(names))
        if missing:
            fail("Recovered zip is missing required files.", detail={"missing": missing, "zip_members": names})
        zf.extractall(out_dir)
    for csv_name in REQUIRED_ZIP_MEMBERS:
        csv_path = out_dir / csv_name
        payload = csv_path.read_bytes()
        if payload.startswith(b"\xef\xbb\xbf"):
            csv_path.write_bytes(payload[3:])
    return names


def read_csv_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        try:
            return next(reader)
        except StopIteration:
            fail("CSV is empty.", detail=str(path))


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        try:
            next(reader)
        except StopIteration:
            return 0
        return sum(1 for _ in reader)


def read_codebook_variables(path: Path, source: str) -> tuple[list[str], list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            fail("raw_codebook.csv has no header.", detail=str(path))
        if source == "elsa":
            required_fields = ["Variable", "newname"]
            missing_fields = [field for field in required_fields if field not in reader.fieldnames]
            if missing_fields:
                fail(
                    "ELSA raw_codebook.csv is missing required identity columns.",
                    detail={"fields": reader.fieldnames, "missing": missing_fields},
                )
            rows = list(reader)
            source_identities = [row.get("Variable", "").strip() for row in rows]
            exported_names = [row.get("newname", "").strip() for row in rows]
            empty_rows = [index + 2 for index, value in enumerate(exported_names) if not value]
            if empty_rows:
                fail(
                    "ELSA raw_codebook.csv contains empty newname values.",
                    detail={"csv_rows": empty_rows},
                )
            duplicates = sorted(
                {value for value in exported_names if exported_names.count(value) > 1}
            )
            if duplicates:
                fail(
                    "ELSA raw_codebook.csv contains duplicated newname values.",
                    detail={"duplicates": duplicates},
                )
            return source_identities, exported_names
        if source == "charls" and "newname" in reader.fieldnames:
            required_fields = ["Variable", "newname"]
            missing_fields = [field for field in required_fields if field not in reader.fieldnames]
            if missing_fields:
                fail(
                    "CHARLS raw_codebook.csv is missing required identity columns.",
                    detail={"fields": reader.fieldnames, "missing": missing_fields},
                )
            rows = list(reader)
            source_identities = [row.get("Variable", "").strip() for row in rows]
            exported_names = [row.get("newname", "").strip() for row in rows]
            empty_rows = [index + 2 for index, value in enumerate(exported_names) if not value]
            if empty_rows:
                fail(
                    "CHARLS raw_codebook.csv contains empty newname values.",
                    detail={"csv_rows": empty_rows},
                )
            duplicates = sorted(
                {value for value in exported_names if exported_names.count(value) > 1}
            )
            if duplicates:
                fail(
                    "CHARLS raw_codebook.csv contains duplicated newname values.",
                    detail={"duplicates": duplicates},
                )
            return source_identities, exported_names
        variable_field = None
        for candidate in ["Variable", "variable", "name", "Name"]:
            if candidate in reader.fieldnames:
                variable_field = candidate
                break
        if variable_field is None:
            fail(
                "Cannot find a variable-name column in raw_codebook.csv.",
                detail={"fields": reader.fieldnames},
            )
        raw_values = [row.get(variable_field, "").strip() for row in reader]
        normalized_values = [normalize_var_name(value) for value in raw_values]
        return raw_values, normalized_values


def exact_match(label: str, actual: Iterable[str], expected: Iterable[str]) -> None:
    actual_list = list(actual)
    expected_list = list(expected)
    if actual_list != expected_list:
        fail(
            f"{label} does not match expected variables exactly.",
            detail={
                "actual": actual_list,
                "expected": expected_list,
                "missing": [item for item in expected_list if item not in actual_list],
                "unexpected": [item for item in actual_list if item not in expected_list],
            },
        )


def expected_header_for_source(source: str, expected_vars: Iterable[str]) -> list[str]:
    vars_list = list(expected_vars)
    if source == "elsa":
        return ["ID", "idauniq"] + vars_list
    return ["ID", "id", "year"] + vars_list


def validate_charls_household_identifier(path: Path) -> dict:
    rows = 0
    derived_keys: set[tuple[str, str]] = set()
    bad_suffix_rows: list[int] = []
    duplicated_rows: list[int] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for csv_row, row in enumerate(reader, start=2):
            rows += 1
            record_id = (row.get("ID") or "").strip()
            year = (row.get("year") or "").strip()
            suffix = f"_{year}"
            if not record_id or not year or not record_id.endswith(suffix):
                bad_suffix_rows.append(csv_row)
                continue
            derived_id = record_id[: -len(suffix)]
            if not derived_id:
                bad_suffix_rows.append(csv_row)
                continue
            key = (derived_id, year)
            if key in derived_keys:
                duplicated_rows.append(csv_row)
            derived_keys.add(key)
    if bad_suffix_rows or duplicated_rows:
        fail(
            "CHARLS household export cannot derive a stable id from ID and year.",
            detail={
                "bad_suffix_rows": bad_suffix_rows[:20],
                "duplicated_id_year_rows": duplicated_rows[:20],
                "rows": rows,
            },
        )
    return {
        "mode": "derived_from_ID_suffix",
        "rows": rows,
        "unique_id_year": len(derived_keys),
    }


def build_report(report: dict) -> str:
    matching_ids = report.get("matching_transaction_ids", [])
    matching_ids_text = ", ".join(str(item) for item in matching_ids)
    lines = [
        "bookapp localhost export recovery QA",
        "",
        f"ok: {report['ok']}",
        f"db: {report['db']}",
        f"transaction: {report['transaction_id']}",
        f"transaction_selection: {report.get('transaction_selection', '')}",
        f"matching_transaction_ids: {matching_ids_text}",
        f"transaction_created_at: {report['transaction_created_at']}",
        f"description: {report['description']}",
        f"out_dir: {report['out_dir']}",
        f"expected_vars: {', '.join(report['expected_vars'])}",
        f"transaction_vars: {', '.join(report['transaction_vars'])}",
    ]
    if report["db"] == "elsa":
        lines.extend(
            [
                f"expected_header: {', '.join(report['expected_header'])}",
                f"actual_header: {', '.join(report['raw_data_header'])}",
                f"variable_file_renames: {'; '.join(report['variable_file_renames'])}",
            ]
        )
    lines.extend(
        [
        f"zip_members: {', '.join(report['zip_members'])}",
        f"raw_data_header: {', '.join(report['raw_data_header'])}",
        f"raw_data_rows: {report['raw_data_rows']}",
        f"raw_data_cols: {report['raw_data_cols']}",
        f"identifier_mode: {report.get('identifier_mode', 'standard')}",
        f"identifier_unique_id_year: {report.get('identifier_unique_id_year', '')}",
        f"raw_codebook_rows: {report['raw_codebook_rows']}",
        f"raw_codebook_vars: {', '.join(report['raw_codebook_vars'])}",
        "",
        "result: PASS",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    global BOOKAPP_ROOT
    args = parse_args()
    configured_bookapp_root = args.bookapp_root or os.environ.get("DBCODEBOOK_BOOKAPP_ROOT")
    if not configured_bookapp_root:
        fail(
            "Bookapp root is not configured. Pass --bookapp-root or set DBCODEBOOK_BOOKAPP_ROOT."
        )
    BOOKAPP_ROOT = Path(configured_bookapp_root).resolve()
    if not BOOKAPP_ROOT.is_dir():
        fail("Bookapp root does not exist.", detail=str(BOOKAPP_ROOT))

    expected_vars = parse_expected_vars(args.expect_vars)
    expected_db = args.db.strip().lower()
    out_dir = args.out.resolve()
    temp_media_root = out_dir / "_bookapp_tmp_media"

    ensure_bookapp_venv()
    prepare_output_dir(out_dir, args.overwrite)
    setup_django(temp_media_root)

    if bool(args.transaction) == bool(args.latest):
        fail("Pass exactly one of --transaction or --latest.")

    transaction = (
        get_latest_matching_transaction(expected_db, expected_vars, args.latest_limit)
        if args.latest
        else get_transaction(args.transaction)
    )
    source = transaction_source(transaction)
    if source != expected_db:
        fail(
            "Transaction source does not match --db.",
            detail={"transaction_source": source, "expected_db": expected_db},
        )

    variables = transaction.variables or []
    transaction_vars = [
        var.get("label") or normalize_var_name(var.get("name", ""))
        for var in variables
    ]
    exact_match("Transaction variable list", transaction_vars, expected_vars)

    columns = build_columns(source, variables)
    response = export_response(source, transaction, columns)
    zip_members = write_zip_and_extract(response, out_dir)

    raw_data_path = out_dir / "raw_data.csv"
    raw_codebook_path = out_dir / "raw_codebook.csv"
    expected_header = expected_header_for_source(source, expected_vars)
    raw_data_header = read_csv_header(raw_data_path)
    identifier_qa = {"mode": "standard", "unique_id_year": ""}
    charls_household_header = ["ID", "year"] + expected_vars
    if source == "charls" and raw_data_header == charls_household_header:
        identifier_qa = validate_charls_household_identifier(raw_data_path)
    else:
        exact_match("raw_data.csv header", raw_data_header, expected_header)

    raw_codebook_vars_raw, raw_codebook_vars = read_codebook_variables(raw_codebook_path, source)
    exact_match("raw_codebook.csv variables", raw_codebook_vars, expected_vars)

    report = {
        "ok": True,
        "db": source,
        "transaction_id": transaction.id,
        "transaction_selection": "latest" if args.latest else "explicit",
        "matching_transaction_ids": getattr(transaction, "_matching_transaction_ids", [transaction.id]),
        "transaction_created_at": (
            transaction.created_at.isoformat()
            if getattr(transaction, "created_at", None)
            else ""
        ),
        "description": transaction.description,
        "out_dir": str(out_dir),
        "expected_vars": expected_vars,
        "transaction_vars": transaction_vars,
        "expected_header": expected_header,
        "variable_file_renames": [
            f"{source_identity} -> {exported_name}"
            for source_identity, exported_name in zip(raw_codebook_vars_raw, raw_codebook_vars)
        ],
        "zip_members": zip_members,
        "raw_data_header": raw_data_header,
        "raw_data_rows": count_csv_rows(raw_data_path),
        "raw_data_cols": len(raw_data_header),
        "identifier_mode": identifier_qa["mode"],
        "identifier_unique_id_year": identifier_qa["unique_id_year"],
        "raw_codebook_rows": len(raw_codebook_vars),
        "raw_codebook_vars_raw": raw_codebook_vars_raw,
        "raw_codebook_vars": raw_codebook_vars,
        "files": {
            "bookapp_download.zip": str(out_dir / "bookapp_download.zip"),
            "raw_data.csv": str(raw_data_path),
            "raw_codebook.csv": str(raw_codebook_path),
            "recover_bookapp_export_QA.txt": str(out_dir / "recover_bookapp_export_QA.txt"),
        },
    }

    qa_text = build_report(report)
    (out_dir / "recover_bookapp_export_QA.txt").write_text(qa_text, encoding="utf-8")
    shutil.rmtree(temp_media_root, ignore_errors=True)
    print(qa_text)
    print("")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

"""Self-check a variable-definition output directory before validation.

This tool is intentionally generic. It checks the repeated mechanical issues
that should not reach the validation thread: forbidden files, raw headers,
analysis workbook columns, codebook variables, and final log status.
"""

from __future__ import annotations

import argparse
import csv
import fnmatch
import html
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


NS_MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
NS_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
NS_PACKAGE_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"


def split_csv(value: str | None) -> list[str]:
    if value is None:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def normalize_var(value: str) -> str:
    return value.split(" (", 1)[0].strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check definition output artifacts.")
    parser.add_argument(
        "--db",
        choices=["charls", "elsa"],
        default="charls",
        help="Database identity mode. Defaults to charls for backward compatibility.",
    )
    parser.add_argument("--formal-dir", required=True, type=Path)
    parser.add_argument("--process-dir", type=Path)
    parser.add_argument("--expected-files", help="Comma-separated required file names.")
    parser.add_argument("--raw-vars", help="Comma-separated expected raw variables after database identity columns.")
    parser.add_argument("--analysis-db", help="Analysis db xlsx file name in formal dir.")
    parser.add_argument("--analysis-columns", help="Comma-separated expected analysis db columns.")
    parser.add_argument("--analysis-codebook", help="Analysis codebook xlsx file name in formal dir.")
    parser.add_argument("--analysis-vars", help="Comma-separated expected analysis variables.")
    parser.add_argument(
        "--check-summary-facts",
        action="store_true",
        help="Reconcile the five-column summary table with analysis workbooks and scan summary indentation.",
    )
    parser.add_argument("--forbid-vars", help="Comma-separated variables that must not appear.")
    parser.add_argument(
        "--required-user-text",
        help="Comma-separated reader-facing facts required in both the note and definition HTML.",
    )
    parser.add_argument(
        "--criteria-evolution-text",
        help="Comma-separated cross-period identity lines required in Criteria 注意点, in display order with br separation.",
    )
    parser.add_argument("--log-prefix", help="Expected final log prefix, e.g. CHARLS_drinking_status.")
    parser.add_argument("--require-log-exit-code", action="store_true")
    parser.add_argument("--max-md", type=int, default=1)
    parser.add_argument("--report", type=Path, help="Optional QA report path.")
    return parser.parse_args()


def fail(results: list[dict], check: str, detail: object) -> None:
    results.append({"ok": False, "check": check, "detail": detail})


def ok(results: list[dict], check: str, detail: object = None) -> None:
    payload = {"ok": True, "check": check}
    if detail is not None:
        payload["detail"] = detail
    results.append(payload)


def read_csv_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        return next(reader)


def count_csv_records(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        return sum(1 for _ in reader)


def read_codebook_vars(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            return []
        candidates = ["newname", "Variable", "variable", "name"]
        column = next((item for item in candidates if item in reader.fieldnames), reader.fieldnames[0])
        return [normalize_var(row.get(column, "")) for row in reader if row.get(column, "").strip()]


def expected_raw_header(db: str, raw_vars: list[str]) -> list[str]:
    if db == "elsa":
        return ["ID", "idauniq", *raw_vars]
    return ["ID", "id", "year", *raw_vars]


def check_charls_household_identifier(path: Path) -> dict:
    rows = 0
    keys: set[tuple[str, str]] = set()
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
            if key in keys:
                duplicated_rows.append(csv_row)
            keys.add(key)
    return {
        "ok": not bad_suffix_rows and not duplicated_rows,
        "mode": "derived_from_ID_suffix",
        "rows": rows,
        "unique_id_year": len(keys),
        "bad_suffix_rows": bad_suffix_rows[:20],
        "duplicated_id_year_rows": duplicated_rows[:20],
    }


def read_elsa_codebook(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        missing_columns = [name for name in ["Variable", "newname"] if name not in fieldnames]
        if missing_columns:
            raise ValueError(f"ELSA codebook missing columns: {', '.join(missing_columns)}")
        rows = list(reader)

    exported_names = [(row.get("newname") or "").strip() for row in rows]
    if any(not name for name in exported_names):
        raise ValueError("ELSA codebook newname must not be empty")
    if len(exported_names) != len(set(exported_names)):
        raise ValueError("ELSA codebook newname must be unique")

    return exported_names


def col_to_index(cell_ref: str) -> int:
    letters = "".join(ch for ch in cell_ref if ch.isalpha())
    total = 0
    for ch in letters:
        total = total * 26 + (ord(ch.upper()) - ord("A") + 1)
    return total - 1


def load_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    values: list[str] = []
    for si in root.findall(f"{NS_MAIN}si"):
        pieces = [node.text or "" for node in si.iter(f"{NS_MAIN}t")]
        values.append("".join(pieces))
    return values


def first_sheet_path(zf: zipfile.ZipFile) -> str:
    workbook = ET.fromstring(zf.read("xl/workbook.xml"))
    rel_id = workbook.find(f"{NS_MAIN}sheets/{NS_MAIN}sheet").attrib[f"{NS_REL}id"]
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    for rel in rels.findall(f"{NS_PACKAGE_REL}Relationship"):
        if rel.attrib["Id"] == rel_id:
            target = rel.attrib["Target"]
            return "xl/" + target.lstrip("/")
    raise ValueError("First worksheet relationship not found.")


def read_xlsx_rows(path: Path) -> list[list[object]]:
    with zipfile.ZipFile(path) as zf:
        shared_strings = load_shared_strings(zf)
        sheet_xml = zf.read(first_sheet_path(zf))
    root = ET.fromstring(sheet_xml)
    rows: list[list[object]] = []
    for row in root.iter(f"{NS_MAIN}row"):
        values: list[object] = []
        for cell in row.findall(f"{NS_MAIN}c"):
            idx = col_to_index(cell.attrib.get("r", "A1"))
            while len(values) <= idx:
                values.append(None)
            value_node = cell.find(f"{NS_MAIN}v")
            if value_node is None:
                value = None
            elif cell.attrib.get("t") == "s":
                value = shared_strings[int(value_node.text)]
            else:
                raw = value_node.text or ""
                if re.fullmatch(r"-?\d+(\.\d+)?", raw):
                    number = float(raw)
                    value = int(number) if number.is_integer() else number
                else:
                    value = raw
            values[idx] = value
        rows.append(values)
    return rows


def check_forbidden_files(formal_dir: Path, results: list[dict], max_md: int) -> None:
    files = [path for path in formal_dir.iterdir() if path.is_file()]
    forbidden_patterns = ["*_defined.csv", "*.rds", "*consistency*disclosure*.xlsx"]
    forbidden = [
        path.name
        for path in files
        if any(fnmatch.fnmatch(path.name.lower(), pattern.lower()) for pattern in forbidden_patterns)
    ]
    if forbidden:
        fail(results, "forbidden files", forbidden)
    else:
        ok(results, "forbidden files")

    md_files = [path.name for path in files if path.suffix.lower() == ".md"]
    if len(md_files) > max_md:
        fail(results, "markdown count", md_files)
    else:
        ok(results, "markdown count", md_files)


def check_logs(formal_dir: Path, log_prefix: str | None, require_exit_code: bool, results: list[dict]) -> None:
    logs = sorted(formal_dir.glob("*.log"))
    if len(logs) != 1:
        fail(results, "single final log", [path.name for path in logs])
        return
    log = logs[0]
    if log_prefix and not log.name.startswith(f"{log_prefix}_run_"):
        fail(results, "log prefix", log.name)
    else:
        ok(results, "log prefix", log.name)

    text = log.read_text(encoding="utf-8", errors="replace")
    problems = [item for item in ["NativeCommandError", "Execution halted"] if item in text]
    if problems:
        fail(results, "log error markers", problems)
    else:
        ok(results, "log error markers")

    if require_exit_code and "Rscript exit code: 0" not in text:
        fail(results, "log exit code", "Rscript exit code: 0 not found")
    else:
        ok(results, "log exit code")


def is_nonmissing(value: object) -> bool:
    return value is not None and str(value).strip() != ""


def period_text(periods: list[int], prefix: str = "Wave", all_periods: list[int] | None = None) -> str:
    values = sorted(set(periods))
    if all_periods is not None and values == sorted(set(all_periods)):
        return "全周期"
    ranges: list[str] = []
    start = previous = values[0]
    for value in values[1:] + [None]:
        if value is not None and value == previous + 1:
            previous = value
            continue
        if prefix:
            ranges.append(f"{prefix} {start}" if start == previous else f"{prefix} {start}-{previous}")
        else:
            ranges.append(f"{start}" if start == previous else f"{start}-{previous}")
        if value is not None:
            start = previous = value
    return "、".join(ranges)


def object_text(
    period_stats: list[tuple[int, int, int]],
    threshold: float = 0.85,
    split_gap: float = 0.20,
    prefix: str = "Wave",
) -> str:
    rates = [(period, nonmissing / total) for period, nonmissing, total in period_stats if nonmissing > 0 and total > 0]
    if not rates:
        raise ValueError("summary variable has no covered period")
    if all(rate >= threshold for _, rate in rates):
        return "全样本"

    low = [(period, rate) for period, rate in rates if rate < threshold]
    high = [(period, rate) for period, rate in rates if rate >= threshold]
    parts: list[str] = []
    if high:
        parts.append(f"{period_text([period for period, _ in high], prefix)} 全样本")
    rounded_groups: dict[float, list[int]] = {}
    for period, rate in low:
        rounded_groups.setdefault(round(rate * 10) * 10, []).append(period)
    for percent in sorted(rounded_groups, reverse=True):
        parts.append(f"{period_text(rounded_groups[percent], prefix)} 约 {percent:g}% 样本")
    return "；<br>".join(parts)


def parse_summary_table(note_text: str) -> list[dict[str, str]]:
    lines = note_text.splitlines()
    header = "| 定义变量 | 含义 | 组成 | 覆盖周期 | 对象 |"
    positions = [index for index, line in enumerate(lines) if line.strip() == header]
    if len(positions) != 1:
        raise ValueError(f"summary table header count must be 1, got {len(positions)}")
    rows: list[dict[str, str]] = []
    for line in lines[positions[0] + 2 :]:
        if not line.strip().startswith("|"):
            break
        cells = [item.strip() for item in line.strip().strip("|").split("|")]
        if len(cells) != 5:
            raise ValueError(f"summary row must have 5 cells: {line}")
        rows.append(
            {
                "Variable": cells[0].strip("`"),
                "meaning": cells[1],
                "raw_count": cells[2],
                "period": cells[3],
                "object": cells[4],
            }
        )
    return rows


def check_summary_prose(note_text: str, results: list[dict]) -> None:
    section = re.search(
        r"(?ms)^## 摘要导读\s*$\n(.*?)^\| 定义变量 \| 含义 \| 组成 \| 覆盖周期 \| 对象 \|\s*$",
        note_text,
    )
    if not section:
        fail(results, "summary prose structure", "summary prose before five-column table not found")
        return
    prose = section.group(1).strip()
    card_pattern = (
        r"(?s)<!-- summary-insight-card:start -->.*?"
        r"<!-- summary-insight-card:end -->"
    )
    card_blocks = re.findall(card_pattern, note_text)
    prose_without_cards = re.sub(card_pattern, "", prose).strip()
    paragraphs = [
        re.sub(r"\s+", " ", part).strip()
        for part in re.split(r"\n\s*\n", prose_without_cards)
        if part.strip()
    ]
    def summary_span_nodes(attribute: str) -> list[tuple[str, str]]:
        return re.findall(
            rf'(?s)(<span[^>]*{re.escape(attribute)}="true"[^>]*>)(.*?)</span>',
            prose_without_cards,
        )

    brand_nodes = summary_span_nodes("data-summary-brand")
    path_nodes = summary_span_nodes("data-summary-path")
    count_nodes = summary_span_nodes("data-summary-count")
    measure_nodes = summary_span_nodes("data-summary-measure")
    concept_nodes = summary_span_nodes("data-summary-concept")

    path_style_ok = all(
        "color:" in tag.lower() and "font-style:italic" in tag.replace(" ", "").lower()
        for tag, _ in path_nodes
    )
    numeric_pattern = re.compile(r"^(?:\d[\d,]*|[一二三四五六七八九十百千万两]+)$")
    count_style_ok = all(
        "color:" in tag.lower()
        and bool(numeric_pattern.fullmatch(re.sub(r"<[^>]+>", "", text).strip()))
        for tag, text in count_nodes
    )
    measure_style_ok = (
        len(measure_nodes) == len(count_nodes)
        and all("white-space:nowrap" in tag.replace(" ", "").lower() for tag, _ in measure_nodes)
    )
    concept_style_ok = all(
        "color:" in tag.lower()
        and (
            "font-weight" not in tag.lower()
            or "font-weight:400" in tag.replace(" ", "").lower()
        )
        for tag, _ in concept_nodes
    )
    concept_quote_count = len(re.findall(
        r'“<span[^>]*data-summary-concept="true"[^>]*>.*?</span>”',
        prose_without_cards,
        re.S,
    ))
    def concept_marks_first_occurrence(tag: str, text: str) -> bool:
        clean_text = re.sub(r"<[^>]+>", "", text).strip()
        full_node = f"{tag}{text}</span>"
        node_start = prose_without_cards.find(full_node)
        text_offset = full_node.find(clean_text)
        return (
            bool(clean_text)
            and node_start >= 0
            and text_offset >= 0
            and prose_without_cards.find(clean_text) == node_start + text_offset
        )

    concept_first_occurrence_ok = all(
        concept_marks_first_occurrence(tag, text)
        for tag, text in concept_nodes
    )
    emphasis_ok = (
        not brand_nodes
        and bool(path_nodes)
        and path_style_ok
        and len(count_nodes) >= 2
        and count_style_ok
        and measure_style_ok
        and bool(concept_nodes)
        and concept_style_ok
        and concept_quote_count == len(concept_nodes)
        and concept_first_occurrence_ok
    )
    banned = [
        "本轮", "见下方", "完整对应关系列在下方", "具体规则保留在定义说明中",
        "使用时先判断", "十项全部有效", "反向计分", "hopeful", "happy",
    ]
    hits = sorted({term for paragraph in paragraphs for term in banned if term in paragraph})
    card_ok = True
    marker_counts_ok = (
        note_text.count("<!-- summary-insight-card:start -->")
        == note_text.count("<!-- summary-insight-card:end -->")
        == len(card_blocks)
    )
    if len(card_blocks) > 1 or not marker_counts_ok:
        card_ok = False
    elif card_blocks:
        card = card_blocks[0]
        title_match = re.search(
            r'(?s)<div[^>]*data-summary-insight-title="true"[^>]*>(.*?)</div>',
            card,
        )
        body_match = re.search(
            r'(?s)<div[^>]*data-summary-insight-body="true"[^>]*>(.*?)</div>',
            card,
        )
        title_text = (
            re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", title_match.group(1))).strip()
            if title_match else ""
        )
        body_text = (
            re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", body_match.group(1))).strip()
            if body_match else ""
        )
        item_matches = re.findall(
            r'(?s)<p[^>]*data-summary-insight-item="true"[^>]*>(.*?)</p>',
            card,
        )
        item_numbers = "①②③④⑤⑥⑦⑧⑨⑩"
        circled_items = re.findall(f"[{item_numbers}]", body_text)
        item_sequence_ok = (
            not circled_items
            or (
                len(circled_items) >= 2
                and len(circled_items) <= len(item_numbers)
                and circled_items == list(item_numbers[:len(circled_items)])
            )
        )
        card_ok = (
            'data-summary-insight-card="true"' in card
            and title_text == "小book提示"
            and bool(body_text)
            and "font-style:italic" not in card.replace(" ", "").lower()
            and "background:#F4F3F0" in card
            and "border:1px solid #F4F3F0" in card
            and item_sequence_ok
            and not item_matches
        )
    legacy_quote_card = bool(re.search(r"(?m)^>\s*", prose_without_cards))
    if legacy_quote_card:
        card_ok = False
    details = {
        "paragraph_count": len(paragraphs),
        "summary_emphasis_ok": emphasis_ok,
        "summary_path_count": len(path_nodes),
        "summary_count_count": len(count_nodes),
        "summary_measure_count": len(measure_nodes),
        "summary_concept_count": len(concept_nodes),
        "insight_card_count": len(card_blocks),
        "insight_card_ok": card_ok,
        "insight_item_count": len(circled_items) if card_blocks else 0,
        "legacy_quote_card": legacy_quote_card,
        "banned": hits,
    }
    if not 1 <= len(paragraphs) <= 2 or hits or not emphasis_ok or not card_ok:
        fail(results, "summary prose lint", details)
    else:
        ok(results, "summary prose lint", details)


def extract_public_r_code(note_text: str) -> str:
    marker = "### 2-代码材料"
    marker_pos = note_text.find(marker)
    if marker_pos < 0:
        raise ValueError("public R section not found")
    fenced = re.search(r"```r\s*\n(.*?)\n```", note_text[marker_pos:], flags=re.DOTALL)
    if not fenced:
        raise ValueError("public R fenced code not found after code-material heading")
    return fenced.group(1)


def check_public_code_outline(
    formal_dir: Path,
    note_text: str,
    results: list[dict],
    db: str,
) -> None:
    scripts = sorted(formal_dir.glob("define*.R"))
    if len(scripts) != 1:
        fail(results, "public R outline source", [path.name for path in scripts])
        return
    source = scripts[0].read_text(encoding="utf-8", errors="replace")
    boundary = re.search(r"(?m)^# 输出\s*$", source)
    if not boundary:
        fail(results, "public R outline boundary", "# 输出 not found")
        return
    source_public = source[: boundary.start()].strip()
    try:
        note_public = extract_public_r_code(note_text).strip()
    except ValueError as exc:
        fail(results, "public R outline extraction", str(exc))
        return
    if note_public != source_public:
        fail(results, "public R source synchronization", "note public code differs from formal R before # 输出")
    else:
        ok(results, "public R source synchronization")

    structural_issues: list[str] = []
    redundant_renames = [
        pattern
        for pattern in [
            r'(?m)^names\(dt\)\[1\]\s*<-\s*["\']ID["\']\s*$',
            r'(?m)^names\(name_z\)\[1\]\s*<-\s*["\']Easy\.label["\']\s*$',
        ]
        if re.search(pattern, source_public)
    ]
    if redundant_renames:
        structural_issues.append("redundant first-column renaming")

    uses_check_names_false = bool(re.search(
        r'read\.csv\([^)]*check\.names\s*=\s*FALSE',
        source_public,
        flags=re.I | re.S,
    ))
    if uses_check_names_false:
        structural_issues.append(
            "read.csv(check.names = FALSE) is forbidden; assign unique aliases in dbCodeBook before download"
        )

    if re.search(r'\[\[\s*["\']Easy label["\']\s*\]\]', source_public):
        structural_issues.append(
            'read.csv normalizes "Easy label" to "Easy.label"; use the normalized column name'
        )

    if db == "charls":
        for raw_name in ("raw_data.csv", "raw_codebook.csv"):
            raw_path = formal_dir / raw_name
            if raw_path.exists() and raw_path.read_bytes().startswith(b"\xef\xbb\xbf"):
                structural_issues.append(
                    f"{raw_name} contains a UTF-8 BOM; fix the export instead of adding read.csv options"
                )
        raw_data_path = formal_dir / "raw_data.csv"
        if raw_data_path.exists():
            raw_header = read_csv_header(raw_data_path)
            duplicate_header = sorted({
                name for name in raw_header if raw_header.count(name) > 1
            })
            if duplicate_header:
                structural_issues.append(
                    "raw_data.csv contains duplicate columns; assign unique aliases "
                    f"in dbCodeBook before download: {', '.join(duplicate_header)}"
                )
        if 'name_z <- read.csv("raw_codebook.csv")' not in source_public:
            structural_issues.append(
                'CHARLS public R must use the simple read: '
                'name_z <- read.csv("raw_codebook.csv")'
            )
        simple_data_read = 'dt <- read.csv("raw_data.csv")' in source_public
        if not simple_data_read:
            structural_issues.append(
                'CHARLS public R must use dt <- read.csv("raw_data.csv")'
            )
        if re.search(r"(?m)^names\((?:data|dt)\)\s*\[[^\]]+\]\s*<-", source_public):
            structural_issues.append(
                "CHARLS public R must not rename raw columns by position; "
                "assign unique aliases in dbCodeBook before download"
            )
        if re.search(
            r'read\.csv\(\s*["\']raw_(?:data|codebook)\.csv["\'][^)]*'
            r'(?:fileEncoding|encoding|col\.names)\s*=',
            source_public,
            flags=re.I,
        ):
            structural_issues.append(
                "CHARLS public raw reads must not add encoding or column-name options"
            )

    if re.search(r"(?m)^raw_row_count\s*<-\s*nrow\(data\)\s*$", source_public):
        structural_issues.append("background raw_row_count leaked into public R")
    if re.search(r"(?m)^raw_vars\s*<-\s*name_z\$newname\s*$", source_public):
        structural_issues.append("raw_vars detours through raw_codebook in public R")
    if re.search(
        r'(?m)^if\s*\(\s*!"id"\s*%in%\s*names\((?:data|dt)\)\s*\)\s*\{',
        source_public,
    ):
        structural_issues.append("defensive id fallback leaked into public R")
    if re.search(
        r"(?ms)^data\s*<-\s*data\s*%>%\s*\n?\s*filter\(year\s*%in%",
        source_public,
    ):
        structural_issues.append(
            "global target-wave filter belongs at the formal output boundary, not the read block"
        )

    required_header_tokens = [
        'library("devtools")',
        'library("openxlsx")',
        'library("dplyr")',
        'install_github("ZhidoHuang/dbCodeBookr")',
        'library("dbCodeBookr")',
    ]
    missing_header_tokens = [
        token for token in required_header_tokens if token not in source_public
    ]
    if missing_header_tokens:
        structural_issues.append(
            "nonstandard package header: missing " + ", ".join(missing_header_tokens)
        )

    if re.search(
        r'for\s*\(\s*pkg\s+in\s+c\([^)]*["\']dbCodeBookr["\']',
        source_public,
        flags=re.I | re.S,
    ):
        structural_issues.append("dbCodeBookr placed in generic package loop")

    if re.search(
        r"(?mi)^#\s*raw_data\.csv.*dbcodebook\.cn.*Go to.*$",
        source_public,
    ):
        structural_issues.append(
            "reader-facing raw_data.csv guide leaked into formal definition R"
        )

    public_lines = source_public.splitlines()
    recode_comment = re.compile(
        r"^\s*#\s*recode\.(chr|num)\(([^)]+)\)\s*$"
    )
    for index, line in enumerate(public_lines):
        match = recode_comment.match(line)
        if not match:
            continue
        target = match.group(2).strip()
        next_index = index + 1
        while next_index < len(public_lines) and not public_lines[next_index].strip():
            next_index += 1
        if next_index >= len(public_lines):
            structural_issues.append(
                f"orphan recode.{match.group(1)} marker for {target}"
            )
            continue
        assignment = public_lines[next_index].strip()
        if not re.match(rf"^{re.escape(target)}\s*<-", assignment):
            structural_issues.append(
                f"recode.{match.group(1)} marker target differs from assignment: {target}"
            )
            continue
        block_lines = [assignment]
        for block_line in public_lines[next_index + 1:]:
            block_lines.append(block_line)
            if re.match(r"^\s*\)\)?\s*$", block_line):
                break
        block = "\n".join(block_lines)
        if block.count(target) < 2:
            structural_issues.append(
                f"recode.{match.group(1)} marker does not recode its own target: {target}"
            )

    if structural_issues:
        fail(results, "public R structural contract", structural_issues)
    else:
        ok(results, "public R structural contract")

    heading_pattern = re.compile(r"(?m)^# -----------\s+(.+?)\s+-----------\s*$")
    headings = heading_pattern.findall(note_public)
    semantic_patterns = [
        ("packages", r"包|环境"),
        ("read data", r"读取.*数据|数据读取"),
        ("definition", r"重编码|分波次|处理|计分|定义"),
        ("variable dictionary", r"^变量字典$"),
        ("formal output", r"正式输出"),
    ]
    matched_positions: list[int] = []
    missing: list[str] = []
    for label, pattern in semantic_patterns:
        position = next((i for i, heading in enumerate(headings) if re.search(pattern, heading, re.I)), None)
        if position is None:
            missing.append(label)
        else:
            matched_positions.append(position)
    if len(headings) < 5 or missing or matched_positions != sorted(matched_positions):
        fail(results, "public R outline", {"headings": headings, "missing": missing})
    else:
        ok(results, "public R outline", headings)

    analysis_match = re.search(r"(?ms)^analysis_vars\s*<-\s*c\((.*?)\)\s*$", source_public)
    analysis_vars = re.findall(r'["\']([^"\']+)["\']', analysis_match.group(1)) if analysis_match else []
    mapped_vars = re.findall(
        r'map\s*<-\s*add_mapping\(\s*map\s*,\s*["\']([^"\']+)["\']\s*,',
        source_public,
    )
    dictionary_match = re.search(
        r"(?ms)^# -----------\s+变量字典\s+-----------\s*$\n(.*?)^# -----------\s+正式输出\s+-----------\s*$",
        source_public,
    )
    dictionary = dictionary_match.group(1) if dictionary_match else ""
    bypass = re.findall(
        r"codebook\$(?:original_vars|processed_vars|count)\s*\[.*?\]\s*<-",
        dictionary,
    )
    map_drives_codebook = all(
        token in dictionary
        for token in ["add_mapping <- function", "map <- data.frame", "codebook <- lapply", "map$Variable", "map$original_vars"]
    )
    missing_mapping = [variable for variable in analysis_vars if variable not in mapped_vars]
    if not analysis_vars or missing_mapping or bypass or not map_drives_codebook:
        fail(results, "add_mapping variable dictionary", {
            "analysis_vars": analysis_vars,
            "mapped_vars": mapped_vars,
            "missing": missing_mapping,
            "direct_codebook_bypass": bypass,
            "map_drives_codebook": map_drives_codebook,
        })
    else:
        ok(results, "add_mapping variable dictionary", analysis_vars)


def extract_category_pairs(text: str) -> list[tuple[str, str]]:
    label_matches = [
        *re.finditer(
            r"<summary>\s*((?:[^<]+?\s+)?(?:source|defined) variables?)\s*</summary>",
            text,
            flags=re.I,
        ),
        *re.finditer(
            r"<a\s+href=\"#cat-[^\"]+\"[^>]*>\s*((?:[^<]+?\s+)?(?:source|defined) variables?)\s*</a>",
            text,
            flags=re.I,
        ),
    ]
    labels = [match.group(1) for match in sorted(label_matches, key=lambda item: item.start())]
    pairs: list[tuple[str, str]] = []
    for label in labels:
        normalized = " ".join(label.split())
        match = re.fullmatch(
            r"(?:(.+?)\s+)?(source|defined) variables?",
            normalized,
            flags=re.I,
        )
        if match:
            category = match.group(1).strip().lower() if match.group(1) else ""
            pairs.append((category, match.group(2).lower()))
    return pairs


def check_category_order(formal_dir: Path, note_text: str, results: list[dict]) -> None:
    detail_files = sorted(formal_dir.glob("*_detail.html"))
    if len(detail_files) != 1:
        fail(results, "detail category order source", [path.name for path in detail_files])
        return
    materials = {
        "detail HTML": detail_files[0].read_text(encoding="utf-8", errors="replace"),
        "note": note_text,
    }
    failures: dict[str, object] = {}
    for name, text in materials.items():
        pairs = extract_category_pairs(text)
        valid = bool(pairs) and len(pairs) % 2 == 0
        if valid:
            for index in range(0, len(pairs), 2):
                valid = valid and pairs[index][1] == "source" and pairs[index + 1][1] == "defined"
                valid = valid and pairs[index][0] == pairs[index + 1][0]
        if not valid:
            failures[name] = pairs
    if failures:
        fail(results, "detail/note category order", failures)
    else:
        ok(results, "detail/note category order", {name: extract_category_pairs(text) for name, text in materials.items()})


def check_summary_facts(
    formal_dir: Path,
    analysis_db_name: str | None,
    analysis_codebook_name: str | None,
    results: list[dict],
    db: str,
) -> None:
    if not analysis_db_name or not analysis_codebook_name:
        fail(results, "summary facts inputs", "--analysis-db and --analysis-codebook are required")
        return

    notes = sorted(formal_dir.glob("*.md"))
    if len(notes) != 1:
        fail(results, "summary note", [path.name for path in notes])
        return
    note_text = notes[0].read_text(encoding="utf-8", errors="replace")
    user_materials = [*notes, *sorted(formal_dir.glob("*.html"))]
    indented = [path.name for path in user_materials if "&emsp;" in path.read_text(encoding="utf-8", errors="replace")]
    if indented:
        fail(results, "summary prose indentation", indented)
    else:
        ok(results, "summary prose indentation", "&emsp; indentation entities = 0")

    try:
        summary_rows = parse_summary_table(note_text)
    except ValueError as exc:
        fail(results, "summary table structure", str(exc))
        return

    check_summary_prose(note_text, results)

    circular = [
        row["Variable"]
        for row in summary_rows
        if re.search(r"有.*(?:题目信息|变量信息)|非缺失者", row["object"])
    ]
    if circular:
        fail(results, "summary circular object", circular)
    else:
        ok(results, "summary circular object")

    db_rows = read_xlsx_rows(formal_dir / analysis_db_name)
    cb_rows = read_xlsx_rows(formal_dir / analysis_codebook_name)
    db_header = [str(value) if value is not None else "" for value in db_rows[0]]
    cb_header = [str(value) if value is not None else "" for value in cb_rows[0]]
    for required in ["Variable", "original_vars", "Label"]:
        if required not in cb_header:
            fail(results, "summary codebook fields", f"missing {required}")
            return
    period_name = "wave" if "wave" in db_header else "year" if "year" in db_header else None
    if period_name is None:
        fail(results, "summary period field", "analysis_db requires wave or year")
        return
    period_prefix = "" if period_name == "year" else "Wave"

    cb_variables: list[str] = []
    expected: list[dict[str, str]] = []
    var_idx = cb_header.index("Variable")
    source_idx = cb_header.index("original_vars")
    label_idx = cb_header.index("Label")
    period_idx = db_header.index(period_name)
    for cb_row in cb_rows[1:]:
        if len(cb_row) <= var_idx or not is_nonmissing(cb_row[var_idx]):
            continue
        variable = str(cb_row[var_idx])
        cb_variables.append(variable)
        if variable not in db_header:
            fail(results, "summary variable in analysis_db", variable)
            return
        value_idx = db_header.index(variable)
        totals: dict[int, list[int]] = {}
        for row in db_rows[1:]:
            if len(row) <= period_idx or not is_nonmissing(row[period_idx]):
                continue
            period = int(float(str(row[period_idx])))
            totals.setdefault(period, [0, 0])
            totals[period][1] += 1
            value = row[value_idx] if len(row) > value_idx else None
            if is_nonmissing(value):
                totals[period][0] += 1
        stats = [(period, counts[0], counts[1]) for period, counts in sorted(totals.items())]
        covered = [period for period, nonmissing, _ in stats if nonmissing > 0]
        sources = str(cb_row[source_idx] if len(cb_row) > source_idx and cb_row[source_idx] is not None else "")
        unique_sources = list(dict.fromkeys(item.strip() for item in sources.split(",") if item.strip()))
        label = str(cb_row[label_idx] if len(cb_row) > label_idx and cb_row[label_idx] is not None else "").strip()
        expected.append(
            {
                "Variable": variable,
                "raw_count": str(len(unique_sources)),
                "period": period_text(covered, period_prefix, sorted(totals)),
                "object": object_text(stats, prefix=period_prefix),
                "label": label,
            }
        )

    actual_variables = [row["Variable"] for row in summary_rows]
    if actual_variables == cb_variables:
        ok(results, "summary variables and order", actual_variables)
    else:
        fail(results, "summary variables and order", {"expected": cb_variables, "actual": actual_variables})

    mismatches: list[dict[str, object]] = []
    expected_by_var = {row["Variable"]: row for row in expected}
    for row in summary_rows:
        fact = expected_by_var.get(row["Variable"])
        if fact is None:
            continue
        wrong = {
            field: {"expected": fact[field], "actual": row[field]}
            for field in ["raw_count", "period", "object"]
            if row[field] != fact[field]
        }
        if not row["meaning"] or not fact["label"]:
            wrong["meaning_review"] = {"meaning": row["meaning"], "Label": fact["label"]}
        if wrong:
            mismatches.append({"Variable": row["Variable"], "fields": wrong})
    if mismatches:
        fail(results, "summary facts", mismatches)
    else:
        ok(results, "summary facts", {"rows": len(summary_rows), "fields": ["raw_count", "period", "object"]})

    wrong_period_terms = []
    for row in summary_rows:
        combined = f"{row['period']} {row['object']}"
        if period_name == "year" and ("Year" in combined or "Wave" in combined or "覆盖波次" in combined):
            wrong_period_terms.append(row["Variable"])
        if period_name == "wave" and ("Year" in combined or "覆盖年份" in combined):
            wrong_period_terms.append(row["Variable"])
    if wrong_period_terms:
        fail(results, "summary period terminology", wrong_period_terms)
    else:
        ok(results, "summary period terminology", {"period_col": period_name, "prefix": period_prefix})

    display_policy = {
        "charls_full": period_text([2011, 2013, 2015], "", [2011, 2013, 2015]),
        "charls_partial": period_text([2011, 2015], "", [2011, 2013, 2015]),
        "elsa_partial": period_text([1, 2, 4], "Wave", [1, 2, 3, 4]),
    }
    expected_policy = {
        "charls_full": "全周期",
        "charls_partial": "2011、2015",
        "elsa_partial": "Wave 1-2、Wave 4",
    }
    if display_policy != expected_policy:
        fail(results, "database period display policy", display_policy)
    else:
        ok(results, "database period display policy", display_policy)

    check_public_code_outline(formal_dir, note_text, results, db)
    check_category_order(formal_dir, note_text, results)


def visible_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value))).strip()


def check_required_user_text(formal_dir: Path, required: list[str], results: list[dict]) -> None:
    if not required:
        return
    notes = sorted(formal_dir.glob("*.md"))
    definitions = sorted(formal_dir.glob("*definition*.html"))
    if len(notes) != 1 or len(definitions) != 1:
        fail(results, "required user text sources", {
            "notes": [path.name for path in notes],
            "definitions": [path.name for path in definitions],
        })
        return
    note_text = visible_text(notes[0].read_text(encoding="utf-8", errors="replace"))
    definition_text = visible_text(definitions[0].read_text(encoding="utf-8", errors="replace"))
    missing = {
        "note": [item for item in required if item not in note_text],
        "definition": [item for item in required if item not in definition_text],
    }
    missing = {name: values for name, values in missing.items() if values}
    if missing:
        fail(results, "required user text", missing)
    else:
        ok(results, "required user text", required)


def visible_text_with_breaks(value: str) -> str:
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.I)
    value = html.unescape(re.sub(r"<[^>]+>", " ", value))
    return re.sub(r"[ \t]+", " ", value)


def check_criteria_evolution(formal_dir: Path, required: list[str], results: list[dict]) -> None:
    if not required:
        return
    definitions = sorted(formal_dir.glob("*definition*.html"))
    notes = sorted(formal_dir.glob("*.md"))
    if len(definitions) != 1 or len(notes) != 1:
        fail(results, "Criteria evolution sources", {
            "definitions": [path.name for path in definitions],
            "notes": [path.name for path in notes],
        })
        return
    definition_text = visible_text_with_breaks(definitions[0].read_text(encoding="utf-8", errors="replace"))
    note_text = visible_text_with_breaks(notes[0].read_text(encoding="utf-8", errors="replace"))
    positions = [definition_text.find(item) for item in required]
    ordered = all(position >= 0 for position in positions) and positions == sorted(positions)
    first = positions[0] if ordered else -1
    last = positions[-1] + len(required[-1]) if ordered else -1
    evolution_block = definition_text[first:last] if ordered else ""
    separated = ordered and all("\n" in definition_text[positions[index] + len(required[index]):positions[index + 1]] for index in range(len(required) - 1))
    attention_before = ordered and definition_text.rfind("注意点：", 0, first) > definition_text.rfind("定义逻辑：", 0, first)
    note_complete = all(item in note_text for item in required)
    if not ordered or not separated or not attention_before or not note_complete:
        fail(results, "Criteria evolution structure", {
            "ordered": ordered,
            "br_separated": separated,
            "under_attention": attention_before,
            "note_complete": note_complete,
            "block": evolution_block,
        })
    else:
        ok(results, "Criteria evolution structure", required)


def criteria_wording_issues(value: str) -> list[str]:
    text = visible_text_with_breaks(value)
    issues: list[str] = []
    for banned in ("明确回答", "明确记录"):
        if banned in text:
            issues.append(f"banned wording: {banned}")

    mechanical_patterns = {
        "single-question recode uses 有效回答": r"有效回答为\s*\[?\s*(?:Yes|No|1|0)\b",
        "single-record assignment uses 有效记录": r"有效记录为\s*\[?\s*(?:Yes|No|1|0)\b",
        "source correspondence is a separate numbered item": (
            r"[①②③④⑤⑥⑦⑧⑨⑩]\s*"
            r"(?:对应原始变量|对应来源|原始变量对应|来源对应|raw\s*变量对应)\s*[：:]"
        ),
        "raw conflict disclosure is vague": r"可能因此呈现不一致组合",
        "raw conflict disclosure uses engineering override wording": (
            r"不用其中一组来源覆盖另一组"
        ),
    }
    for label, pattern in mechanical_patterns.items():
        if re.search(pattern, text, flags=re.I):
            issues.append(label)
    if "保留原始矛盾" in text and "不做相互修正" not in text:
        issues.append("raw conflict preservation lacks no-mutual-correction statement")
    return issues


def check_criteria_wording(formal_dir: Path, results: list[dict]) -> None:
    definitions = sorted(formal_dir.glob("*definition*.html"))
    if len(definitions) != 1:
        fail(results, "Criteria wording sources", {
            "definitions": [path.name for path in definitions],
        })
        return
    issues = criteria_wording_issues(
        definitions[0].read_text(encoding="utf-8", errors="replace")
    )
    if issues:
        fail(results, "Criteria wording", issues)
    else:
        ok(results, "Criteria wording", {
            "banned": ["明确回答", "明确记录"],
            "mechanical_single_item_phrases": [
                "有效回答为 [Yes/No/1/0]",
                "有效记录为 [Yes/No/1/0]",
                "单独编号的对应原始变量/对应来源",
                "可能因此呈现不一致组合",
                "不用其中一组来源覆盖另一组",
            ],
        })


def check_forbidden_formal_content(formal_dir: Path, forbidden: set[str], results: list[dict]) -> None:
    if not forbidden:
        return
    findings: list[dict[str, str]] = []
    text_suffixes = {".r", ".md", ".html", ".csv", ".txt", ".log"}
    for path in sorted(formal_dir.iterdir()):
        if path.is_file() and path.suffix.lower() in text_suffixes:
            content = path.read_text(encoding="utf-8-sig", errors="replace")
            for value in forbidden:
                if value in content:
                    findings.append({"file": path.name, "value": value})
        if path.is_file() and path.suffix.lower() == ".xlsx":
            for row in read_xlsx_rows(path):
                row_text = " ".join("" if value is None else str(value) for value in row)
                for value in forbidden:
                    if value in row_text:
                        findings.append({"file": path.name, "value": value})
    if findings:
        fail(results, "forbidden formal content", findings)
    else:
        ok(results, "forbidden formal content", sorted(forbidden))


def main() -> int:
    args = parse_args()
    results: list[dict] = []
    formal_dir = args.formal_dir

    if not formal_dir.exists():
        fail(results, "formal dir exists", str(formal_dir))
        print(json.dumps({"ok": False, "checks": results}, ensure_ascii=False, indent=2))
        return 1
    ok(results, "formal dir exists", str(formal_dir))

    expected_files = split_csv(args.expected_files)
    for name in expected_files:
        path = formal_dir / name
        if path.exists():
            ok(results, f"required file: {name}")
        else:
            fail(results, f"required file: {name}", str(path))

    check_forbidden_files(formal_dir, results, args.max_md)

    raw_vars = split_csv(args.raw_vars)
    forbid_vars = set(split_csv(args.forbid_vars))
    required_user_text = split_csv(args.required_user_text)
    criteria_evolution_text = split_csv(args.criteria_evolution_text)
    if raw_vars:
        raw_data = formal_dir / "raw_data.csv"
        raw_codebook = formal_dir / "raw_codebook.csv"
        expected_header = expected_raw_header(args.db, raw_vars)
        header = read_csv_header(raw_data)
        if header == expected_header:
            ok(results, "raw_data header", header)
        elif args.db == "charls" and header == ["ID", "year", *raw_vars]:
            identifier_check = check_charls_household_identifier(raw_data)
            if identifier_check["ok"]:
                ok(
                    results,
                    "raw_data header",
                    {
                        "header": header,
                        "identifier": identifier_check,
                    },
                )
            else:
                fail(
                    results,
                    "raw_data header",
                    {
                        "expected": expected_header,
                        "actual": header,
                        "identifier": identifier_check,
                    },
                )
        else:
            fail(results, "raw_data header", {"expected": expected_header, "actual": header})
        ok(results, "raw_data rows", count_csv_records(raw_data))

        try:
            if args.db == "elsa":
                codebook_vars = read_elsa_codebook(raw_codebook)
            else:
                codebook_vars = read_codebook_vars(raw_codebook)
        except ValueError as exc:
            codebook_vars = []
            fail(results, "raw_codebook structure", str(exc))
        if codebook_vars == raw_vars:
            ok(results, "raw_codebook vars", codebook_vars)
        else:
            fail(results, "raw_codebook vars", {"expected": raw_vars, "actual": codebook_vars})

        forbidden_found = sorted(forbid_vars.intersection(set(header + codebook_vars)))
        if forbidden_found:
            fail(results, "forbidden vars in raw/codebook", forbidden_found)
        else:
            ok(results, "forbidden vars in raw/codebook")

    if args.analysis_db:
        rows = read_xlsx_rows(formal_dir / args.analysis_db)
        header = [str(item) if item is not None else "" for item in rows[0]]
        expected_columns = split_csv(args.analysis_columns)
        if expected_columns and header != expected_columns:
            fail(results, "analysis_db columns", {"expected": expected_columns, "actual": header})
        else:
            ok(results, "analysis_db columns", header)
        ok(results, "analysis_db dimensions", {"rows": len(rows) - 1, "cols": len(header)})

        forbidden_found = sorted(forbid_vars.intersection(set(header)))
        if forbidden_found:
            fail(results, "forbidden vars in analysis_db", forbidden_found)
        else:
            ok(results, "forbidden vars in analysis_db")

    if args.analysis_codebook:
        rows = read_xlsx_rows(formal_dir / args.analysis_codebook)
        header = [str(item) if item is not None else "" for item in rows[0]]
        try:
            var_idx = header.index("Variable")
        except ValueError:
            var_idx = 0
        variables = [str(row[var_idx]) for row in rows[1:] if len(row) > var_idx and row[var_idx] is not None]
        expected_vars = split_csv(args.analysis_vars)
        if expected_vars and variables != expected_vars:
            fail(results, "analysis_codebook vars", {"expected": expected_vars, "actual": variables})
        else:
            ok(results, "analysis_codebook vars", variables)

    if args.check_summary_facts:
        check_summary_facts(
            formal_dir,
            args.analysis_db,
            args.analysis_codebook,
            results,
            args.db,
        )

    check_required_user_text(formal_dir, required_user_text, results)
    check_criteria_evolution(formal_dir, criteria_evolution_text, results)
    check_criteria_wording(formal_dir, results)
    check_forbidden_formal_content(formal_dir, forbid_vars, results)

    check_logs(formal_dir, args.log_prefix, args.require_log_exit_code, results)

    passed = all(item["ok"] for item in results)
    payload = {"ok": passed, "checks": results}
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    print(text)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text + "\n", encoding="utf-8")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

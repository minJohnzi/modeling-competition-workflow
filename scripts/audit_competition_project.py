#!/usr/bin/env python3
"""Read-only structural and reproducibility audit for mathematical-modeling projects.

Checks structural conventions, strict JSON, real SHA-256 input hashes, CSV
numerical sanity, dual-format figures (.png + optional .pdf/.svg), run logs,
flexible paper drafts, header-aware ARTIFACT_REGISTRY.md status consistency,
and absolute-path / anonymity leak markers.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import struct
import sys
import tempfile
import zlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


QUESTION_RE = re.compile(r"^q(\d+)$", re.IGNORECASE)
FIGURE_PNG_RE = re.compile(r"^fig(\d{2})_[a-z0-9][a-z0-9_]*\.png$", re.IGNORECASE)
FIGURE_VEC_RE = re.compile(r"^fig(\d{2})_[a-z0-9][a-z0-9_]*\.(pdf|svg)$", re.IGNORECASE)
SHA256_HEX_RE = re.compile(r"^[0-9a-fA-F]{64}$")
ABSOLUTE_PATH_PATTERNS = (
    re.compile(r"[A-Za-z]:\\(?:[^\\\r\n]+\\)*[^\\\r\n]*"),
    re.compile(r"/Users/[^\s)>\]]+"),
    re.compile(r"/home/[^\s)>\]]+"),
)
ANONYMITY_MARKERS = (
    "队号",
    "学校",
    "大学",
    "指导教师",
)
STATUS_TOKENS = (
    "PENDING_MAIN_REVIEW",
    "PROVISIONAL",
    "SUPPORTED",
    "INVALID",
    "STALE",
    "ARCHIVED",
    "VALID",
)
REQUIRED_PAPER_STAGES = (
    "01_problem_analysis.md",
    "02_data_analysis.md",
    "03_model.md",
    "04_validation.md",
    "05_conclusion.md",
)
CSV_BAD_TOKENS = {"nan", "inf", "-inf", "+inf", "infinity", "-infinity", "null"}
MIN_SINGLE_DRAFT_CHARS = 200


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    path: str
    message: str


class Audit:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.findings: list[Finding] = []

    def add(self, severity: str, code: str, path: Path, message: str) -> None:
        try:
            shown = str(path.resolve().relative_to(self.root.resolve()))
        except (OSError, ValueError):
            shown = str(path)
        self.findings.append(Finding(severity, code, shown or ".", message))

    def error(self, code: str, path: Path, message: str) -> None:
        self.add("ERROR", code, path, message)

    def warning(self, code: str, path: Path, message: str) -> None:
        self.add("WARNING", code, path, message)

    def info(self, code: str, path: Path, message: str) -> None:
        self.add("INFO", code, path, message)

    def counts(self) -> dict[str, int]:
        return {
            severity: sum(item.severity == severity for item in self.findings)
            for severity in ("ERROR", "WARNING", "INFO")
        }


def reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant: {value}")


def load_strict_json(path: Path) -> Any:
    text = path.read_text(encoding="utf-8-sig")
    return json.loads(text, parse_constant=reject_json_constant)


def compute_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_input_hashes(value: Any, found: list[tuple[str, str]]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            key_str = str(key).lower()
            if key_str in {"input_hashes", "data_hashes"} and isinstance(child, dict):
                for file_key, hash_val in child.items():
                    if isinstance(hash_val, str):
                        found.append((str(file_key), hash_val.strip()))
            else:
                collect_input_hashes(child, found)
    elif isinstance(value, list):
        for child in value:
            collect_input_hashes(child, found)


def nested_has_key(value: Any, needle: str) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if needle in str(key).lower() or nested_has_key(child, needle):
                return True
    elif isinstance(value, list):
        return any(nested_has_key(child, needle) for child in value)
    return False


def resolve_input_file(root: Path, question: Path, key_name: str) -> Path | None:
    normalized = key_name.replace("\\", "/").lstrip("./")
    candidates = [
        question / normalized,
        question / "data" / normalized,
        question / "data" / Path(normalized).name,
        root / normalized,
        root / "data" / normalized,
        root / "data" / Path(normalized).name,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def verify_input_hashes(audit: Audit, root: Path, question: Path, summary_path: Path, summary: dict[str, Any]) -> None:
    pairs: list[tuple[str, str]] = []
    collect_input_hashes(summary, pairs)
    if not pairs:
        if not nested_has_key(summary, "hash"):
            audit.warning("summary-missing-input-hash", summary_path, "机器摘要未发现输入哈希字段")
        return

    for key_name, expected_hash in pairs:
        if not SHA256_HEX_RE.fullmatch(expected_hash):
            audit.warning(
                "unverified-input-hash-placeholder",
                summary_path,
                f"输入哈希 {key_name}={expected_hash!r} 不是标准 64 位 SHA-256 十六进制串",
            )
            continue
        target = resolve_input_file(root, question, key_name)
        if target is None:
            audit.warning(
                "input-hash-file-not-found",
                summary_path,
                f"未能定位哈希条目对应的输入文件：{key_name}",
            )
            continue
        actual_hash = compute_sha256(target)
        if actual_hash.lower() != expected_hash.lower():
            audit.error(
                "input-hash-mismatch",
                target,
                f"输入文件 SHA-256 与摘要不一致：期望 {expected_hash[:12]}...，实际 {actual_hash[:12]}...",
            )


def png_dpi(path: Path) -> tuple[float, float] | None:
    with path.open("rb") as handle:
        if handle.read(8) != b"\x89PNG\r\n\x1a\n":
            raise ValueError("not a PNG file")
        while True:
            raw_length = handle.read(4)
            if not raw_length:
                return None
            if len(raw_length) != 4:
                raise ValueError("truncated PNG chunk length")
            length = struct.unpack(">I", raw_length)[0]
            chunk_type = handle.read(4)
            data = handle.read(length)
            crc = handle.read(4)
            if len(chunk_type) != 4 or len(data) != length or len(crc) != 4:
                raise ValueError("truncated PNG chunk")
            if chunk_type == b"pHYs":
                if length != 9:
                    raise ValueError("invalid pHYs chunk")
                x_ppm, y_ppm, unit = struct.unpack(">IIB", data)
                if unit != 1:
                    return None
                return x_ppm * 0.0254, y_ppm * 0.0254
            if chunk_type == b"IEND":
                return None


def extract_machine_status(summary: Any) -> str | None:
    if not isinstance(summary, dict):
        return None
    for key in ("status", "formal_validation_status", "validation_status"):
        value = summary.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().upper()
    return None


def status_class(status: str | None) -> str | None:
    if status in {"VALID", "SUPPORTED"}:
        return "supported"
    if status in {"PROVISIONAL", "PENDING_MAIN_REVIEW"}:
        return "pending"
    if status in {"INVALID", "STALE"}:
        return "invalid"
    if status == "ARCHIVED":
        return "archived"
    return status.lower() if status else None


def find_header_index(headers: list[str], keywords: tuple[str, ...], fallback: int) -> int:
    for idx, header in enumerate(headers):
        normalized = header.strip().lower()
        if any(kw in normalized for kw in keywords):
            return idx
    return fallback if fallback < len(headers) else -1


def artifact_registry_status(root: Path, question_name: str) -> str | None:
    registry = root / "ARTIFACT_REGISTRY.md"
    if not registry.is_file():
        return None
    text = registry.read_text(encoding="utf-8-sig", errors="replace")
    lines = text.splitlines()

    q_col, art_col, status_col = 0, 1, 2
    in_table = False
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("|"):
            in_table = False
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not in_table:
            if idx + 1 < len(lines) and re.match(r"^\s*\|[\s:\-\|]+\|\s*$", lines[idx + 1]):
                q_col = find_header_index(cells, ("问题", "question"), 0)
                art_col = find_header_index(cells, ("产物", "artifact"), 1)
                status_col = find_header_index(cells, ("状态", "status"), 2)
                in_table = True
            continue
        if re.match(r"^\s*\|[\s:\-\|]+\|\s*$", stripped):
            continue
        if max(q_col, art_col, status_col) >= len(cells):
            continue
        q_val = cells[q_col].upper()
        art_val = cells[art_col].upper()
        status_val = cells[status_col]
        if q_val == question_name.upper() and "RESULT_SUMMARY.JSON" in art_val:
            for token in STATUS_TOKENS:
                if re.search(rf"\b{re.escape(token)}\b", status_val, flags=re.IGNORECASE):
                    return token
    return None


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


def check_absolute_paths_and_anonymity(
    audit: Audit, paths: Iterable[Path], check_anonymity: bool = False
) -> None:
    for path in paths:
        if not path.is_file():
            continue
        text = read_text(path)
        for pattern in ABSOLUTE_PATH_PATTERNS:
            match = pattern.search(text)
            if match:
                audit.warning(
                    "absolute-path-in-formal-doc",
                    path,
                    f"发现疑似本机绝对路径：{match.group(0)[:100]}",
                )
                break
        if check_anonymity:
            for marker in ANONYMITY_MARKERS:
                if marker in text:
                    audit.warning(
                        "possible-anonymity-leak",
                        path,
                        f"发现疑似匿名敏感词 `{marker}`，请核对是否合规",
                    )
                    break


def check_csv_tables(audit: Audit, tables: Sequence[Path]) -> None:
    for table in tables:
        try:
            with table.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.reader(handle))
        except (OSError, UnicodeError, csv.Error) as exc:
            audit.error("invalid-csv", table, f"CSV 读取失败：{exc}")
            continue
        if len(rows) < 2:
            audit.warning("empty-csv-table", table, "CSV 缺少数据行（仅为空表或只有表头）")
            continue
        bad_found = False
        for row in rows[1:]:
            for cell in row:
                if cell.strip().lower() in CSV_BAD_TOKENS:
                    bad_found = True
                    break
            if bad_found:
                break
        if bad_found:
            audit.warning("csv-contains-nan-or-inf", table, "CSV 含有 NaN / Inf / null 异常值")


def check_run_log(audit: Audit, path: Path) -> None:
    if not path.is_file():
        audit.error("missing-run-log", path, "缺少 outputs/run_log.md")
        return
    text = read_text(path).lower()
    checks = (
        (("command", "命令"), "run-log-command", "运行日志未记录执行命令"),
        (("seed", "随机种子", "deterministic", "确定性"), "run-log-seed", "运行日志未记录随机种子或确定性"),
        (("hash", "sha-256", "sha256", "哈希"), "run-log-hash", "运行日志未记录输入哈希"),
        (("runtime", "耗时", "duration"), "run-log-runtime", "运行日志未记录可靠运行时长"),
        (("test", "测试", "验证"), "run-log-tests", "运行日志未记录测试或验证"),
    )
    for needles, code, message in checks:
        if not any(needle in text for needle in needles):
            audit.warning(code, path, message)


def check_output_readme_count(audit: Audit, outputs: Path, figures: Sequence[Path]) -> None:
    index = outputs / "README.md"
    if not index.is_file() or not figures:
        return
    numbers = [int(match) for match in re.findall(r"fig(\d{2})", read_text(index), flags=re.IGNORECASE)]
    actual = [int(match.group(1)) for path in figures if (match := FIGURE_PNG_RE.match(path.name))]
    if numbers and actual and max(numbers) < max(actual):
        audit.warning(
            "output-index-stale",
            index,
            f"输出索引最高记录 fig{max(numbers):02d}，实际正式图达到 fig{max(actual):02d}",
        )


def check_paper_drafts(audit: Audit, paper: Path, question_name: str, paper_mode: str) -> None:
    if not paper.is_dir():
        return

    stage_paths = [paper / name for name in REQUIRED_PAPER_STAGES]
    any_stage_exists = any(path.is_file() for path in stage_paths)
    all_stages_exist = all(path.is_file() for path in stage_paths)

    single_candidates = [
        path
        for path in sorted(paper.glob("*.md"))
        if (
            path.name.lower().startswith("section_")
            or path.name.lower() == "formal_section.md"
            or question_name.lower() in path.name.lower()
        )
        and len(read_text(path).strip()) >= MIN_SINGLE_DRAFT_CHARS
    ]

    if paper_mode == "stages" or (paper_mode == "auto" and any_stage_exists):
        for path in stage_paths:
            if not path.is_file():
                audit.error("missing-paper-stage", path, f"缺少持续论文草稿 {path.name}")
    elif paper_mode == "single":
        if not single_candidates:
            audit.error(
                "missing-paper-draft",
                paper,
                f"未发现有效的单文件章节草稿（如 section_{question_name.lower()}.md 或 formal_section.md，且不少于 {MIN_SINGLE_DRAFT_CHARS} 字符）",
            )
    else:
        if not all_stages_exist and not single_candidates:
            audit.error(
                "missing-paper-draft",
                paper,
                "未发现五阶段草稿（01..05_*.md）或完整的单文件章节草稿（section_*.md / formal_section.md）",
            )

    formal_docs = sorted(paper.glob("*.md"))
    check_absolute_paths_and_anonymity(audit, formal_docs, check_anonymity=True)


def audit_question(audit: Audit, question: Path, min_dpi: float, paper_mode: str) -> None:
    audit.info("question-discovered", question, f"审计 {question.name}")

    for dirname in ("data", "src", "outputs", "paper"):
        directory = question / dirname
        if not directory.is_dir():
            audit.error("missing-required-directory", directory, f"缺少 {dirname}/ 目录")

    readme = question / "README.md"
    if not readme.is_file():
        audit.error("missing-question-readme", readme, "缺少问题级 README.md")
    notes = question / "notes.md"
    if not notes.is_file():
        audit.warning("missing-question-notes", notes, "建议集中记录假设、待验证项和结论边界")

    src = question / "src"
    if src.is_dir() and not any(path.is_file() for path in src.iterdir()):
        audit.error("empty-source-directory", src, "src/ 为空")

    data = question / "data"
    if data.is_dir():
        data_files = [path for path in data.rglob("*") if path.is_file() and path.name.lower() != "readme.md"]
        if not data_files:
            audit.warning(
                "no-local-data-files",
                data,
                "data/ 未包含数据文件；若使用共享或根目录数据，应在 README 中明确来源",
            )

    outputs = question / "outputs"
    summary: Any = None
    summary_path = outputs / "result_summary.json"
    if not summary_path.is_file():
        audit.error("missing-result-summary", summary_path, "缺少 outputs/result_summary.json")
    else:
        try:
            summary = load_strict_json(summary_path)
            if not isinstance(summary, dict):
                audit.error("summary-not-object", summary_path, "机器摘要顶层必须为 JSON object")
            else:
                verify_input_hashes(audit, audit.root, question, summary_path, summary)
                if extract_machine_status(summary) is None:
                    audit.warning("summary-missing-status", summary_path, "机器摘要未发现正式状态字段")
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
            audit.error("invalid-strict-json", summary_path, f"严格 JSON 解析失败：{exc}")

    check_run_log(audit, outputs / "run_log.md")

    if outputs.is_dir():
        tables = sorted(outputs.glob("table_*.csv"))
        if not tables:
            audit.error("missing-formal-tables", outputs, "未发现 table_*.csv")
        else:
            check_csv_tables(audit, tables)

        figures = sorted(outputs.glob("fig*.png"))
        if not figures:
            audit.error("missing-formal-figures", outputs, "未发现 figNN_meaning.png")
        png_stems = {fig.stem.lower() for fig in figures}
        for figure in figures:
            if not FIGURE_PNG_RE.match(figure.name):
                audit.warning(
                    "nonstandard-figure-name",
                    figure,
                    "正式图建议使用 figNN_lowercase_meaning.png",
                )
            try:
                dpi = png_dpi(figure)
                if dpi is None:
                    audit.warning("missing-png-dpi", figure, "PNG 未记录可解析的物理 DPI")
                elif min(dpi) + 1.0 < min_dpi:
                    audit.error(
                        "low-png-dpi",
                        figure,
                        f"图片 DPI 约为 {dpi[0]:.1f}×{dpi[1]:.1f}，低于 {min_dpi:.0f}",
                    )
            except (OSError, ValueError, struct.error) as exc:
                audit.error("invalid-png", figure, f"PNG 检查失败：{exc}")

        check_output_readme_count(audit, outputs, figures)

        for suffix in (".html", ".svg", ".pdf"):
            for path in sorted(outputs.glob(f"*{suffix}")):
                if (
                    suffix in {".pdf", ".svg"}
                    and FIGURE_VEC_RE.match(path.name)
                    and path.stem.lower() in png_stems
                ):
                    continue
                audit.warning(
                    "non-png-formal-output",
                    path,
                    "正式输出目录含非配套 HTML/SVG/PDF 文件；确认它是允许产物而非历史残留",
                )

    check_paper_drafts(audit, question / "paper", question.name, paper_mode)
    check_absolute_paths_and_anonymity(audit, (readme,), check_anonymity=False)

    if isinstance(summary, dict):
        machine_status = extract_machine_status(summary)
        registry_status = artifact_registry_status(audit.root, question.name)
        if (
            machine_status
            and registry_status
            and status_class(machine_status) != status_class(registry_status)
        ):
            audit.warning(
                "status-registry-conflict",
                summary_path,
                f"机器摘要状态为 {machine_status}，根产物登记为 {registry_status}；需确认状态优先级",
            )


def discover_questions(root: Path, requested: str) -> list[Path]:
    if requested.strip().lower() != "auto":
        names = [item.strip() for item in requested.split(",") if item.strip()]
        return [root / name for name in names]
    questions = [
        path
        for path in root.iterdir()
        if path.is_dir() and QUESTION_RE.fullmatch(path.name)
    ]
    return sorted(questions, key=lambda path: int(QUESTION_RE.fullmatch(path.name).group(1)))


def run_audit(
    root: Path,
    requested: str = "auto",
    min_dpi: float = 300.0,
    paper_mode: str = "auto",
) -> Audit:
    audit = Audit(root)
    if not root.is_dir():
        audit.error("invalid-root", root, "项目根目录不存在或不是目录")
        return audit

    questions = discover_questions(root, requested)
    if not questions:
        audit.error("no-question-directories", root, "未发现 qN/QN 问题目录")
        return audit

    for question in questions:
        if not question.is_dir():
            audit.error("missing-question-directory", question, "指定的问题目录不存在")
            continue
        audit_question(audit, question, min_dpi, paper_mode)

    if len(questions) > 1:
        coordination = (
            "PROJECT_STATE.md",
            "INTERFACE_CONTRACTS.md",
            "ARTIFACT_REGISTRY.md",
        )
        for filename in coordination:
            path = root / filename
            if not path.is_file():
                audit.warning(
                    "missing-multi-question-governance",
                    path,
                    f"多问题项目建议维护 {filename}",
                )

    return audit


def png_chunk(kind: bytes, data: bytes) -> bytes:
    payload = kind + data
    return struct.pack(">I", len(data)) + payload + struct.pack(">I", zlib.crc32(payload) & 0xFFFFFFFF)


def write_test_png(path: Path, dpi: float = 400.0) -> None:
    ppm = round(dpi / 0.0254)
    content = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
        + png_chunk(b"pHYs", struct.pack(">IIB", ppm, ppm, 1))
        + png_chunk(b"IDAT", zlib.compress(b"\x00\xff\xff\xff\xff"))
        + png_chunk(b"IEND", b"")
    )
    path.write_bytes(content)


def self_test() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory(prefix="modeling-audit-") as temp:
        root = Path(temp)
        question = root / "Q1"
        for dirname in ("data", "src", "outputs", "paper"):
            (question / dirname).mkdir(parents=True, exist_ok=True)

        (question / "README.md").write_text("# Q1\n\nRun from the project root.\n", encoding="utf-8")
        (question / "notes.md").write_text("# Notes\n\nNo unresolved assumptions.\n", encoding="utf-8")
        (question / "src" / "run_q1.py").write_text("print('ok')\n", encoding="utf-8")
        input_csv = question / "data" / "input.csv"
        input_csv.write_text("id,value\n1,1\n", encoding="utf-8")
        real_hash = compute_sha256(input_csv)

        (root / "ARTIFACT_REGISTRY.md").write_text(
            "# Registry\n\n"
            "| 产物 | 问题 | 当前状态 | 验证证据 |\n"
            "|---|---|---|---|\n"
            "| `q1/outputs/result_summary.json` | Q1 | SUPPORTED | 10/10 tests |\n",
            encoding="utf-8",
        )

        (question / "outputs" / "result_summary.json").write_text(
            json.dumps(
                {
                    "status": "SUPPORTED",
                    "input_hashes": {"input.csv": real_hash},
                    "random_seed": 42,
                    "constraint_audit": {"passed": True},
                },
                ensure_ascii=False,
                allow_nan=False,
            ),
            encoding="utf-8",
        )
        (question / "outputs" / "table_policy_comparison.csv").write_text(
            "policy,value\nbaseline,1.0\nmain,0.8\n",
            encoding="utf-8",
        )
        (question / "outputs" / "run_log.md").write_text(
            "# Run log\n\nCommand, random seed, SHA-256 hash, runtime, tests passed.\n",
            encoding="utf-8",
        )
        write_test_png(question / "outputs" / "fig01_policy_comparison.png")
        (question / "outputs" / "fig01_policy_comparison.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")
        (question / "paper" / "section_q1.md").write_text(
            "# 5.1 Model Section\n\n"
            + "This section formulates the mathematical model, constraints, baseline comparisons, "
            * 5,
            encoding="utf-8",
        )

        audit = run_audit(root, paper_mode="auto")
        counts = audit.counts()
        if counts["ERROR"] or counts["WARNING"]:
            detail = "; ".join(f"{item.code}: {item.message}" for item in audit.findings)
            return False, f"positive fixture failed: {detail}"

        # Negative checks: tampered data hash, NaN in CSV, NaN in JSON, low PNG DPI, anonymity marker
        input_csv.write_text("id,value\n1,999\n", encoding="utf-8")
        (question / "outputs" / "table_policy_comparison.csv").write_text(
            "policy,value\nbaseline,1.0\nmain,NaN\n",
            encoding="utf-8",
        )
        write_test_png(question / "outputs" / "fig01_policy_comparison.png", dpi=72.0)
        (question / "paper" / "section_q1.md").write_text(
            "# 5.1 Model Section\n\n队号: 12345\n" + ("Valid content. " * 20),
            encoding="utf-8",
        )
        neg_hash_audit = run_audit(root)
        detected = {item.code for item in neg_hash_audit.findings}

        (question / "outputs" / "result_summary.json").write_text(
            '{"status": "SUPPORTED", "value": NaN}',
            encoding="utf-8",
        )
        neg_json_audit = run_audit(root)
        detected |= {item.code for item in neg_json_audit.findings}

        expected = {
            "invalid-strict-json",
            "low-png-dpi",
            "input-hash-mismatch",
            "csv-contains-nan-or-inf",
            "possible-anonymity-leak",
        }
        if not expected.issubset(detected):
            missing = ", ".join(sorted(expected - detected))
            return False, f"negative fixture did not detect: {missing}"

        return True, "positive fixture passed and all negative fixture violations were detected"


def render_text(audit: Audit) -> str:
    counts = audit.counts()
    lines = [
        "Modeling competition project audit",
        f"Root: {audit.root}",
        f"Summary: {counts['ERROR']} error(s), {counts['WARNING']} warning(s), {counts['INFO']} info",
    ]
    for finding in audit.findings:
        lines.append(
            f"[{finding.severity}] {finding.code} | {finding.path} | {finding.message}"
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only structural audit for qN/QN mathematical-modeling competition projects."
    )
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Project root to audit")
    parser.add_argument(
        "--questions",
        default="auto",
        help="Comma-separated question directories, or auto to discover qN/QN directories",
    )
    parser.add_argument(
        "--paper-mode",
        choices=("auto", "stages", "single"),
        default="auto",
        help="Paper draft mode: auto (stages if started, else single), stages (01..05), or single",
    )
    parser.add_argument(
        "--min-dpi",
        type=float,
        default=300.0,
        help="Minimum recorded PNG DPI; default: 300",
    )
    parser.add_argument(
        "--strict-warnings",
        action="store_true",
        help="Return a non-zero exit code when warnings are present",
    )
    parser.add_argument("--json", dest="as_json", action="store_true", help="Emit JSON")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run an isolated fixture test instead of auditing a project",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.min_dpi <= 0:
        print("--min-dpi must be positive", file=sys.stderr)
        return 2

    if args.self_test:
        passed, message = self_test()
        print(f"SELF-TEST {'PASS' if passed else 'FAIL'}: {message}")
        return 0 if passed else 2

    root = args.root.resolve()
    audit = run_audit(root, args.questions, args.min_dpi, args.paper_mode)
    counts = audit.counts()
    if args.as_json:
        payload = {
            "root": str(root),
            "summary": counts,
            "findings": [asdict(item) for item in audit.findings],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False))
    else:
        print(render_text(audit))

    if counts["ERROR"]:
        return 2
    if args.strict_warnings and counts["WARNING"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

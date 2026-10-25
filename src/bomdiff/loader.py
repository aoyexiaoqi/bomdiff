"""BOM 文件加载：CSV / TSV 解析、校验、重复行聚合。

Loading BOM files: CSV/TSV parsing, validation, duplicate aggregation.
"""

from __future__ import annotations

import csv
import io
import os
from typing import List, Optional, TextIO, Union

from .model import Bom, BomItem, Number

REQUIRED_COLUMNS = ("part_number", "description", "qty", "unit")
OPTIONAL_COLUMNS = ("level", "reference")


class BomError(Exception):
    """BOM 文件格式或内容错误。"""


class DuplicatePartError(BomError):
    """严格模式下发现重复 part_number。"""


def _parse_qty(raw: str, lineno: int) -> Number:
    text = (raw or "").strip()
    if text == "":
        raise BomError(f"第 {lineno} 行：qty 为空 (empty qty)")
    try:
        value = float(text)
    except ValueError:
        raise BomError(f"第 {lineno} 行：qty 不是数字：{raw!r}")
    return int(value) if value.is_integer() else value


def _parse_level(raw: str, lineno: int) -> Optional[int]:
    text = (raw or "").strip()
    if text == "":
        return None
    try:
        return int(text)
    except ValueError:
        raise BomError(f"第 {lineno} 行：level 不是整数：{raw!r}")


def parse_bom(stream: TextIO, source: str = "", delimiter: Optional[str] = None,
              strict: bool = False) -> Bom:
    """从文本流解析 BOM。delimiter 为 None 时按表头自动判断（制表符/逗号）。"""
    if delimiter is None:
        pos = stream.tell() if hasattr(stream, "tell") else 0
        head = stream.read(4096)
        if hasattr(stream, "seek"):
            stream.seek(pos)
        first_line = head.splitlines()[0] if head.splitlines() else ""
        delimiter = "\t" if "\t" in first_line else ","

    reader = csv.reader(stream, delimiter=delimiter)
    rows = [row for row in reader if any(cell.strip() for cell in row)]
    if not rows:
        raise BomError(f"{source or 'BOM'}：文件为空，缺少表头 (empty file)")

    header = [cell.strip().lower() for cell in rows[0]]
    missing = [c for c in REQUIRED_COLUMNS if c not in header]
    if missing:
        raise BomError(
            f"{source or 'BOM'}：缺少必需列：{', '.join(missing)} "
            f"(missing required columns)"
        )
    idx = {name: header.index(name) for name in header}

    def cell(row: List[str], name: str) -> str:
        i = idx.get(name)
        if i is None or i >= len(row):
            return ""
        return row[i].strip()

    bom = Bom(source=source)
    counts: dict = {}
    for offset, row in enumerate(rows[1:]):
        lineno = offset + 2  # 表头是第 1 行
        part_number = cell(row, "part_number")
        if not part_number:
            raise BomError(f"第 {lineno} 行：part_number 为空 (empty part_number)")
        item = BomItem(
            part_number=part_number,
            description=cell(row, "description"),
            qty=_parse_qty(cell(row, "qty"), lineno),
            unit=cell(row, "unit"),
            level=_parse_level(cell(row, "level"), lineno) if "level" in idx else None,
            reference=cell(row, "reference"),
        )
        bom.total_lines += 1
        counts[part_number] = counts.get(part_number, 0) + 1
        if part_number in bom.items:
            if strict:
                raise DuplicatePartError(
                    f"{source or 'BOM'}：part_number 重复：{part_number}"
                    f"（第 {lineno} 行，严格模式不允许重复）"
                )
            existing = bom.items[part_number]
            existing.qty = existing.qty + item.qty
        else:
            bom.items[part_number] = item

    for part_number, n in counts.items():
        if n > 1:
            bom.aggregations.append(
                f"{part_number}：出现 {n} 行，qty 已聚合为 "
                f"{bom.items[part_number].qty}"
            )
    return bom


def load_bom(path: Union[str, os.PathLike], strict: bool = False) -> Bom:
    """从文件路径加载 BOM。分隔符按扩展名判断：.tsv 用制表符，其余用逗号，
    扩展名不明确时回退到表头嗅探。"""
    path_str = os.fspath(path)
    delimiter = "\t" if path_str.lower().endswith(".tsv") else None
    with open(path_str, "r", encoding="utf-8-sig", newline="") as fh:
        return parse_bom(fh, source=path_str, delimiter=delimiter, strict=strict)


def loads_bom(text: str, source: str = "", delimiter: Optional[str] = None,
              strict: bool = False) -> Bom:
    """从字符串解析 BOM（便于测试与 API 调用）。"""
    return parse_bom(io.StringIO(text), source=source, delimiter=delimiter,
                     strict=strict)

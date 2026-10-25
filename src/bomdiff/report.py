"""报告渲染：Markdown（人读）与 JSON（机读）。

Report rendering: Markdown for humans, JSON for machines.
"""

from __future__ import annotations

import json
from typing import Optional

from .diff import DiffResult, FieldChange
from .model import BomItem, format_number


def _fmt_value(change: FieldChange) -> str:
    if change.field == "qty":
        return format_number(change.new)  # type: ignore[arg-type]
    return str(change.new)


def _item_row(item: BomItem) -> str:
    return (f"| {item.part_number} | {item.description} | "
            f"{format_number(item.qty)} | {item.unit} |")


def _change_text(change: FieldChange) -> str:
    if change.field == "qty":
        delta = change.delta if change.delta is not None else 0
        sign = "+" if delta > 0 else ""
        return (f"qty：{format_number(change.old)} → "
                f"{format_number(change.new)}（{sign}{format_number(delta)}）")
    return f"{change.field}：{change.old} → {change.new}"


def render_markdown(result: DiffResult) -> str:
    lines = []
    lines.append("# BOM 版本对比报告 / BOM Diff Report")
    lines.append("")
    lines.append(f"- 旧版 BOM (old)：{result.old_source or '-'}"
                 f"（{result.old_total_lines} 行 / {result.old_total_unique} 个零件）")
    lines.append(f"- 新版 BOM (new)：{result.new_source or '-'}"
                 f"（{result.new_total_lines} 行 / {result.new_total_unique} 个零件）")
    lines.append(f"- 新增 (added)：{len(result.added)}")
    lines.append(f"- 删除 (removed)：{len(result.removed)}")
    lines.append(f"- 变更 (changed)：{len(result.changed)}")
    lines.append(f"- 未变 (unchanged)：{result.unchanged_count}")
    lines.append("")

    if result.old_aggregations or result.new_aggregations:
        lines.append("## 重复行聚合说明 (Aggregated duplicates)")
        lines.append("")
        for note in result.old_aggregations:
            lines.append(f"- 旧版：{note}")
        for note in result.new_aggregations:
            lines.append(f"- 新版：{note}")
        lines.append("")

    lines.append(f"## 新增零件 (Added) — {len(result.added)}")
    lines.append("")
    if result.added:
        lines.append("| part_number | description | qty | unit |")
        lines.append("|---|---|---|---|")
        for item in result.added:
            lines.append(_item_row(item))
    else:
        lines.append("（无）")
    lines.append("")

    lines.append(f"## 删除零件 (Removed) — {len(result.removed)}")
    lines.append("")
    if result.removed:
        lines.append("| part_number | description | qty | unit |")
        lines.append("|---|---|---|---|")
        for item in result.removed:
            lines.append(_item_row(item))
    else:
        lines.append("（无）")
    lines.append("")

    lines.append(f"## 变更零件 (Changed) — {len(result.changed)}")
    lines.append("")
    if result.changed:
        for part in result.changed:
            detail = "；".join(_change_text(c) for c in part.changes)
            lines.append(f"- **{part.part_number}**：{detail}")
    else:
        lines.append("（无）")
    lines.append("")

    if result.has_differences:
        lines.append("结论：两张 BOM 存在差异。")
    else:
        lines.append("结论：两张 BOM 无差异 (no differences)。")
    lines.append("")
    return "\n".join(lines)


def _item_dict(item: BomItem) -> dict:
    return {
        "part_number": item.part_number,
        "description": item.description,
        "qty": item.qty,
        "unit": item.unit,
        "level": item.level,
        "reference": item.reference,
    }


def _change_dict(change: FieldChange) -> dict:
    data = {"field": change.field, "old": change.old, "new": change.new}
    if change.field == "qty":
        data["delta"] = change.delta
    return data


def to_dict(result: DiffResult) -> dict:
    return {
        "summary": {
            "old_source": result.old_source,
            "new_source": result.new_source,
            "old_total_lines": result.old_total_lines,
            "new_total_lines": result.new_total_lines,
            "old_part_count": result.old_total_unique,
            "new_part_count": result.new_total_unique,
            "added": len(result.added),
            "removed": len(result.removed),
            "changed": len(result.changed),
            "unchanged": result.unchanged_count,
            "has_differences": result.has_differences,
        },
        "aggregations": {
            "old": list(result.old_aggregations),
            "new": list(result.new_aggregations),
        },
        "added": [_item_dict(i) for i in result.added],
        "removed": [_item_dict(i) for i in result.removed],
        "changed": [
            {"part_number": p.part_number,
             "changes": [_change_dict(c) for c in p.changes]}
            for p in result.changed
        ],
    }


def render_json(result: DiffResult, indent: Optional[int] = 2) -> str:
    return json.dumps(to_dict(result), ensure_ascii=False, indent=indent)

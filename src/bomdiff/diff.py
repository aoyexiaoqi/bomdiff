"""两张 BOM 的对比逻辑。

Diff logic: compare two BOMs part by part, field by field.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .model import Bom, BomItem, Number


@dataclass
class FieldChange:
    """单个字段的变更。qty 变更额外带 delta。"""

    field: str
    old: object
    new: object
    delta: Optional[Number] = None  # 仅 qty 变更时有值


@dataclass
class PartChange:
    """一个零件的多字段变更。"""

    part_number: str
    changes: List[FieldChange] = field(default_factory=list)


@dataclass
class DiffResult:
    old_source: str = ""
    new_source: str = ""
    old_total_lines: int = 0
    new_total_lines: int = 0
    added: List[BomItem] = field(default_factory=list)
    removed: List[BomItem] = field(default_factory=list)
    changed: List[PartChange] = field(default_factory=list)
    unchanged_count: int = 0
    old_aggregations: List[str] = field(default_factory=list)
    new_aggregations: List[str] = field(default_factory=list)

    @property
    def has_differences(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    @property
    def old_part_count(self) -> int:
        return self.old_total_unique

    old_total_unique: int = 0
    new_total_unique: int = 0


def _compare_item(old: BomItem, new: BomItem) -> List[FieldChange]:
    changes: List[FieldChange] = []
    if old.qty != new.qty:
        changes.append(FieldChange(
            field="qty", old=old.qty, new=new.qty, delta=new.qty - old.qty))
    if old.unit != new.unit:
        changes.append(FieldChange(field="unit", old=old.unit, new=new.unit))
    if old.description != new.description:
        changes.append(FieldChange(
            field="description", old=old.description, new=new.description))
    if old.level != new.level:
        changes.append(FieldChange(field="level", old=old.level, new=new.level))
    if old.reference != new.reference:
        changes.append(FieldChange(
            field="reference", old=old.reference, new=new.reference))
    return changes


def diff_boms(old: Bom, new: Bom) -> DiffResult:
    """对比两张已加载的 BOM，返回结构化差异结果。"""
    result = DiffResult(
        old_source=old.source,
        new_source=new.source,
        old_total_lines=old.total_lines,
        new_total_lines=new.total_lines,
        old_aggregations=list(old.aggregations),
        new_aggregations=list(new.aggregations),
    )
    result.old_total_unique = len(old.items)
    result.new_total_unique = len(new.items)

    for part_number in sorted(new.items):
        if part_number not in old.items:
            result.added.append(new.items[part_number])
    for part_number in sorted(old.items):
        if part_number not in new.items:
            result.removed.append(old.items[part_number])
    for part_number in sorted(old.items):
        if part_number not in new.items:
            continue
        changes = _compare_item(old.items[part_number], new.items[part_number])
        if changes:
            result.changed.append(PartChange(part_number=part_number,
                                             changes=changes))
        else:
            result.unchanged_count += 1
    return result

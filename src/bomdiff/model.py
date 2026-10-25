"""数据模型：BOM 行与整张 BOM。

Data model: a single BOM line and a whole BOM.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union

Number = Union[int, float]


def format_number(value: Number) -> str:
    """把数量格式化为简洁字符串：2.0 -> '2'，2.5 -> '2.5'。"""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


@dataclass
class BomItem:
    """BOM 中的一行物料。part_number 是身份键。"""

    part_number: str
    description: str = ""
    qty: Number = 0
    unit: str = ""
    level: Optional[int] = None
    reference: str = ""


@dataclass
class Bom:
    """一张 BOM：按 part_number 索引的行 + 元信息。"""

    items: Dict[str, BomItem] = field(default_factory=dict)
    source: str = ""
    total_lines: int = 0  # 文件中的数据行数（含被聚合的重复行）
    aggregations: List[str] = field(default_factory=list)  # 重复行聚合说明

    def __len__(self) -> int:
        return len(self.items)

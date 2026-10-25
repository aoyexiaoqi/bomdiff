"""bomdiff — BOM（物料清单）版本对比工具。

Bill-of-materials version diff: compare two BOM files (CSV/TSV) and report
added / removed / changed parts, field by field.

示例 (example)::

    from bomdiff import load_bom, diff_boms, render_markdown

    old = load_bom("bom_v1.csv")
    new = load_bom("bom_v2.csv")
    result = diff_boms(old, new)
    print(render_markdown(result))
"""

from .diff import DiffResult, FieldChange, PartChange, diff_boms
from .loader import BomError, DuplicatePartError, load_bom, loads_bom
from .model import Bom, BomItem
from .report import render_json, render_markdown, to_dict

__version__ = "0.1.0"

__all__ = [
    "Bom",
    "BomItem",
    "BomError",
    "DuplicatePartError",
    "DiffResult",
    "FieldChange",
    "PartChange",
    "load_bom",
    "loads_bom",
    "diff_boms",
    "render_markdown",
    "render_json",
    "to_dict",
    "__version__",
]

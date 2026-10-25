"""命令行入口：bomdiff old.csv new.csv [--format md|json] [--strict]

退出码 (exit codes)：
  0 — 两张 BOM 无差异
  1 — 存在差异
  2 — 输入错误（文件不存在、格式错误、严格模式下有重复行等）
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from .diff import diff_boms
from .loader import BomError, load_bom
from .report import render_json, render_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bomdiff",
        description="BOM（物料清单）版本对比工具 / Bill-of-materials version diff",
    )
    parser.add_argument("old", help="旧版 BOM 文件 (CSV/TSV)")
    parser.add_argument("new", help="新版 BOM 文件 (CSV/TSV)")
    parser.add_argument("--format", choices=["md", "json"], default="md",
                        help="输出格式：md=Markdown 报告（默认），json=结构化 JSON")
    parser.add_argument("--strict", action="store_true",
                        help="严格模式：同一文件内出现重复 part_number 时直接报错"
                             "（默认行为是聚合 qty 并注明）")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        old_bom = load_bom(args.old, strict=args.strict)
        new_bom = load_bom(args.new, strict=args.strict)
    except FileNotFoundError as exc:
        print(f"错误：文件不存在：{exc.filename}", file=sys.stderr)
        return 2
    except BomError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2

    result = diff_boms(old_bom, new_bom)
    if args.format == "json":
        print(render_json(result))
    else:
        print(render_markdown(result))
    return 1 if result.has_differences else 0


if __name__ == "__main__":
    raise SystemExit(main())

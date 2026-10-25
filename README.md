# bomdiff

BOM（物料清单）版本对比工具：对比两张 BOM 文件，一眼看清**新增 / 删除 / 变更**了哪些零件，变更细到每个字段（用量及增减量、单位、描述、层级、位号）。纯 Python 标准库实现，提供命令行与 Python API 两种用法，退出码对 CI 友好。

## 功能

- 读取 CSV / TSV 格式 BOM（`.tsv` 按扩展名识别，其余按表头自动嗅探分隔符）
- 以 `part_number` 为身份键，逐字段对比：`qty`（带 delta 增减量）、`unit`、`description`、`level`、`reference`
- 同一文件内重复 `part_number`：默认**聚合 qty** 并在报告中注明；`--strict` 严格模式下直接报错
- 输出 Markdown 报告（人读）或 JSON（机读），报告头部带汇总（新旧总行数、各类计数）
- 退出码：`0` = 无差异，`1` = 有差异，`2` = 输入错误 —— 可直接接入 CI / 变更评审流程

## BOM 文件格式

必需列：`part_number, description, qty, unit`；可选列：`level, reference`。

`examples/bom_v1.csv`（旧版）：

```csv
part_number,description,qty,unit,level,reference
PCB-001,主板 PCB,1,pcs,0,
IC-100,主控芯片,1,pcs,1,U1
R-10K,电阻 10K 0603,12,pcs,1,R1-R12
C-100N,电容 100nF 0603,8,pcs,1,C1-C8
CONN-2P,2P 接线端子,2,pcs,1,J1-J2
BOX-01,外壳,1,pcs,0,
```

`examples/bom_v2.csv`（新版）相对旧版：删除了 `BOX-01`，新增 `LED-RED`，`R-10K` 用量 12 → 16。

## 命令行用法

```bash
pip install -e .

bomdiff examples/bom_v1.csv examples/bom_v2.csv            # Markdown 报告
bomdiff examples/bom_v1.csv examples/bom_v2.csv --format json
bomdiff old.csv new.csv --strict                            # 重复料号直接报错
echo $?   # 0=无差异 1=有差异 2=输入错误
```

示例输出（Markdown）：

```markdown
# BOM 版本对比报告 / BOM Diff Report

- 旧版 BOM (old)：examples/bom_v1.csv（6 行 / 6 个零件）
- 新版 BOM (new)：examples/bom_v2.csv（6 行 / 6 个零件）
- 新增 (added)：1
- 删除 (removed)：1
- 变更 (changed)：1
- 未变 (unchanged)：4

## 新增零件 (Added) — 1

| part_number | description | qty | unit |
|---|---|---|---|
| LED-RED | 红色指示灯 LED | 3 | pcs |

## 删除零件 (Removed) — 1

| part_number | description | qty | unit |
|---|---|---|---|
| BOX-01 | 外壳 | 1 | pcs |

## 变更零件 (Changed) — 1

- **R-10K**：qty：12 → 16（+4）；reference：R1-R12 → R1-R16

结论：两张 BOM 存在差异。
```

## Python API

```python
from bomdiff import load_bom, diff_boms, render_markdown, render_json

old = load_bom("bom_v1.csv")            # strict=True 时重复料号报错
new = load_bom("bom_v2.csv")
result = diff_boms(old, new)

result.added            # [BomItem(...)] 新增零件
result.removed          # [BomItem(...)] 删除零件
result.changed          # [PartChange(...)] 含每个字段的 old/new，qty 带 delta
result.unchanged_count  # 未变零件数
result.has_differences  # bool

print(render_markdown(result))   # 人读报告
print(render_json(result))       # 机读 JSON
```

也可以用 `loads_bom(text)` 直接从字符串解析。

## 开发与测试

```bash
pip install -e ".[test]"
pytest
```

需要 Python ≥ 3.9。CI 在 Python 3.9–3.13 矩阵上运行 pytest。

## License

MIT

---

## English

**bomdiff** compares two bill-of-materials (BOM) files and reports exactly what changed between versions: **added** parts, **removed** parts, and **changed** parts — field by field (quantity with delta, unit, description, level, reference designator). Pure standard library, CLI + Python API, CI-friendly exit codes.

### File format

CSV or TSV with required columns `part_number, description, qty, unit` and optional `level, reference`. `part_number` is the identity key. Duplicate part numbers within one file are aggregated (quantities summed, noted in the report) by default; `--strict` turns them into an error.

### Usage

```bash
bomdiff old.csv new.csv                  # Markdown report
bomdiff old.csv new.csv --format json    # machine-readable JSON
bomdiff old.csv new.csv --strict         # error on duplicate part numbers
```

Exit codes: `0` = no differences, `1` = differences found, `2` = input error.

```python
from bomdiff import load_bom, diff_boms, render_markdown

result = diff_boms(load_bom("bom_v1.csv"), load_bom("bom_v2.csv"))
print(render_markdown(result))
```

Requires Python ≥ 3.9. MIT license.

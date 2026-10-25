"""加载器测试：解析、校验、重复聚合、严格模式、TSV。"""

import pytest

from bomdiff import BomError, DuplicatePartError, load_bom, loads_bom

HEADER = "part_number,description,qty,unit\n"


def test_load_basic_csv():
    bom = loads_bom(HEADER + "A-1,Widget,2,pcs\nB-2,Gadget,3.5,kg\n")
    assert len(bom) == 2
    assert bom.total_lines == 2
    assert bom.items["A-1"].description == "Widget"
    assert bom.items["A-1"].qty == 2
    assert bom.items["B-2"].qty == 3.5
    assert bom.items["B-2"].unit == "kg"


def test_load_optional_columns():
    text = ("part_number,description,qty,unit,level,reference\n"
            "A-1,Widget,2,pcs,1,U1\n")
    bom = loads_bom(text)
    assert bom.items["A-1"].level == 1
    assert bom.items["A-1"].reference == "U1"


def test_load_without_optional_columns():
    bom = loads_bom(HEADER + "A-1,Widget,2,pcs\n")
    assert bom.items["A-1"].level is None
    assert bom.items["A-1"].reference == ""


def test_header_only_file_is_valid_empty_bom():
    bom = loads_bom(HEADER)
    assert len(bom) == 0
    assert bom.total_lines == 0


def test_empty_file_raises():
    with pytest.raises(BomError):
        loads_bom("")


def test_missing_required_column_raises():
    with pytest.raises(BomError) as exc:
        loads_bom("part_number,description,qty\nA-1,Widget,2\n")
    assert "unit" in str(exc.value)


def test_non_numeric_qty_raises():
    with pytest.raises(BomError):
        loads_bom(HEADER + "A-1,Widget,many,pcs\n")


def test_empty_qty_raises():
    with pytest.raises(BomError):
        loads_bom(HEADER + "A-1,Widget,,pcs\n")


def test_empty_part_number_raises():
    with pytest.raises(BomError):
        loads_bom(HEADER + ",Widget,2,pcs\n")


def test_whitespace_is_trimmed():
    bom = loads_bom(HEADER + "  A-1 , Widget , 2 , pcs \n")
    assert "A-1" in bom.items
    assert bom.items["A-1"].description == "Widget"


def test_blank_lines_ignored():
    bom = loads_bom(HEADER + "A-1,Widget,2,pcs\n\n\nB-2,Gadget,1,pcs\n")
    assert len(bom) == 2
    assert bom.total_lines == 2


def test_duplicate_rows_aggregate_qty_by_default():
    text = HEADER + "A-1,Widget,2,pcs\nA-1,Widget,3,pcs\nB-2,Gadget,1,pcs\n"
    bom = loads_bom(text)
    assert len(bom) == 2
    assert bom.total_lines == 3
    assert bom.items["A-1"].qty == 5
    assert len(bom.aggregations) == 1
    assert "A-1" in bom.aggregations[0]


def test_duplicate_aggregation_float_arithmetic():
    text = HEADER + "A-1,Resin,1.5,kg\nA-1,Resin,2.25,kg\n"
    bom = loads_bom(text)
    assert bom.items["A-1"].qty == pytest.approx(3.75)


def test_strict_mode_rejects_duplicates():
    text = HEADER + "A-1,Widget,2,pcs\nA-1,Widget,3,pcs\n"
    with pytest.raises(DuplicatePartError):
        loads_bom(text, strict=True)


def test_strict_mode_accepts_unique_parts():
    bom = loads_bom(HEADER + "A-1,Widget,2,pcs\nB-2,Gadget,1,pcs\n", strict=True)
    assert len(bom) == 2


def test_tsv_sniffed_from_header():
    text = "part_number\tdescription\tqty\tunit\nA-1\tWidget\t2\tpcs\n"
    bom = loads_bom(text)
    assert bom.items["A-1"].qty == 2


def test_tsv_file_by_extension(tmp_path):
    path = tmp_path / "bom.tsv"
    path.write_text(
        "part_number\tdescription\tqty\tunit\nA-1\tWidget\t4\tpcs\n",
        encoding="utf-8")
    bom = load_bom(path)
    assert bom.items["A-1"].qty == 4
    assert bom.source.endswith("bom.tsv")


def test_load_from_csv_file(tmp_path):
    path = tmp_path / "bom.csv"
    path.write_text(HEADER + "A-1,Widget,2,pcs\n", encoding="utf-8")
    bom = load_bom(path)
    assert len(bom) == 1


def test_bom_with_bom_crlf_and_quoted_commas(tmp_path):
    path = tmp_path / "bom.csv"
    path.write_bytes(
        b"\xef\xbb\xbfpart_number,description,qty,unit\r\n"
        b"A-1,\"Bracket, steel\",2,pcs\r\n")
    bom = load_bom(path)
    assert bom.items["A-1"].description == "Bracket, steel"

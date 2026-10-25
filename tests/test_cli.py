"""CLI 测试：退出码与输出格式。"""

import json

from bomdiff.cli import main

HEADER = "part_number,description,qty,unit\n"


def _write(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return str(path)


def test_cli_exit_0_when_identical(tmp_path, capsys):
    old = _write(tmp_path, "old.csv", HEADER + "A-1,X,1,pcs\n")
    new = _write(tmp_path, "new.csv", HEADER + "A-1,X,1,pcs\n")
    assert main([old, new]) == 0
    assert "无差异" in capsys.readouterr().out


def test_cli_exit_1_when_different(tmp_path, capsys):
    old = _write(tmp_path, "old.csv", HEADER + "A-1,X,1,pcs\n")
    new = _write(tmp_path, "new.csv", HEADER + "A-1,X,2,pcs\n")
    assert main([old, new]) == 1
    assert "A-1" in capsys.readouterr().out


def test_cli_json_format_output(tmp_path, capsys):
    old = _write(tmp_path, "old.csv", HEADER + "A-1,X,1,pcs\n")
    new = _write(tmp_path, "new.csv", HEADER + "A-1,X,1,pcs\nB-2,Y,5,pcs\n")
    assert main([old, new, "--format", "json"]) == 1
    data = json.loads(capsys.readouterr().out)
    assert data["summary"]["added"] == 1
    assert data["added"][0]["part_number"] == "B-2"


def test_cli_strict_mode_duplicate_is_error(tmp_path, capsys):
    dup = HEADER + "A-1,X,1,pcs\nA-1,X,2,pcs\n"
    old = _write(tmp_path, "old.csv", dup)
    new = _write(tmp_path, "new.csv", HEADER + "A-1,X,3,pcs\n")
    assert main([old, new, "--strict"]) == 2
    assert "重复" in capsys.readouterr().err


def test_cli_default_mode_aggregates_duplicates(tmp_path):
    dup = HEADER + "A-1,X,1,pcs\nA-1,X,2,pcs\n"
    old = _write(tmp_path, "old.csv", dup)
    new = _write(tmp_path, "new.csv", HEADER + "A-1,X,3,pcs\n")
    # 聚合后两边 A-1 都是 3 → 无差异 → 退出码 0
    assert main([old, new]) == 0


def test_cli_missing_file_exit_2(tmp_path, capsys):
    new = _write(tmp_path, "new.csv", HEADER + "A-1,X,3,pcs\n")
    assert main([str(tmp_path / "nope.csv"), new]) == 2
    assert "不存在" in capsys.readouterr().err


def test_cli_malformed_bom_exit_2(tmp_path):
    old = _write(tmp_path, "old.csv", "part_number,qty\nA-1,3\n")
    new = _write(tmp_path, "new.csv", HEADER + "A-1,X,3,pcs\n")
    assert main([old, new]) == 2


def test_cli_tsv_files(tmp_path):
    old = _write(tmp_path, "old.tsv",
                 "part_number\tdescription\tqty\tunit\nA-1\tX\t1\tpcs\n")
    new = _write(tmp_path, "new.tsv",
                 "part_number\tdescription\tqty\tunit\nA-1\tX\t9\tpcs\n")
    assert main([old, new]) == 1

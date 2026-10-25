"""报告渲染测试：JSON 结构与 Markdown 内容。"""

import json

from bomdiff import diff_boms, loads_bom, render_json, render_markdown, to_dict

HEADER = "part_number,description,qty,unit\n"
OLD = HEADER + "A-1,Old,4,pcs\nB-2,Removed,1,pcs\n"
NEW = HEADER + "A-1,Old,6,pcs\nC-3,Added,2,pcs\n"


def _result():
    return diff_boms(loads_bom(OLD, source="v1.csv"),
                     loads_bom(NEW, source="v2.csv"))


def test_json_schema_top_level_keys():
    data = json.loads(render_json(_result()))
    assert set(data) == {"summary", "aggregations", "added", "removed", "changed"}


def test_json_summary_counts():
    summary = to_dict(_result())["summary"]
    assert summary["added"] == 1
    assert summary["removed"] == 1
    assert summary["changed"] == 1
    assert summary["unchanged"] == 0
    assert summary["has_differences"] is True
    assert summary["old_total_lines"] == 2
    assert summary["new_total_lines"] == 2
    assert summary["old_source"] == "v1.csv"


def test_json_changed_entry_includes_delta():
    data = to_dict(_result())
    change = data["changed"][0]["changes"][0]
    assert data["changed"][0]["part_number"] == "A-1"
    assert change == {"field": "qty", "old": 4, "new": 6, "delta": 2}


def test_json_added_removed_item_fields():
    data = to_dict(_result())
    assert data["added"][0]["part_number"] == "C-3"
    assert data["added"][0]["qty"] == 2
    assert data["removed"][0]["part_number"] == "B-2"
    assert set(data["added"][0]) == {
        "part_number", "description", "qty", "unit", "level", "reference"}


def test_json_round_trip_no_difference():
    same = diff_boms(loads_bom(OLD), loads_bom(OLD))
    data = json.loads(render_json(same))
    assert data["summary"]["has_differences"] is False
    assert data["added"] == [] and data["removed"] == [] and data["changed"] == []


def test_markdown_contains_all_sections_and_parts():
    md = render_markdown(_result())
    assert "BOM 版本对比报告" in md
    assert "新增零件" in md and "C-3" in md
    assert "删除零件" in md and "B-2" in md
    assert "变更零件" in md and "A-1" in md
    assert "未变 (unchanged)：0" in md


def test_markdown_qty_change_shows_arrow_and_delta():
    md = render_markdown(_result())
    assert "qty：4 → 6（+2）" in md


def test_markdown_no_difference_conclusion():
    same = diff_boms(loads_bom(OLD), loads_bom(OLD))
    md = render_markdown(same)
    assert "无差异" in md
    assert "（无）" in md


def test_markdown_includes_aggregation_notes():
    dup = HEADER + "A-1,X,1,pcs\nA-1,X,2,pcs\n"
    result = diff_boms(loads_bom(dup), loads_bom(HEADER + "A-1,X,3,pcs\n"))
    md = render_markdown(result)
    assert "聚合" in md
    assert "A-1" in md

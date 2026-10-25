"""对比逻辑测试：用差异已知的夹具 BOM 对验证每一类变更。"""

from bomdiff import diff_boms, loads_bom

HEADER = "part_number,description,qty,unit,level,reference\n"

OLD = HEADER + (
    "KEEP-1,保持不变,10,pcs,1,\n"
    "QTY-1,用量变化,4,pcs,1,\n"
    "DESC-1,旧描述,2,pcs,1,\n"
    "UNIT-1,单位变化,5,pcs,1,\n"
    "GONE-1,将被删除,7,pcs,1,\n"
)
NEW = HEADER + (
    "KEEP-1,保持不变,10,pcs,1,\n"
    "QTY-1,用量变化,9,pcs,1,\n"
    "DESC-1,新描述,2,pcs,1,\n"
    "UNIT-1,单位变化,5,kg,1,\n"
    "ADD-1,新增零件,3,pcs,1,\n"
)


def _diff():
    return diff_boms(loads_bom(OLD, source="old.csv"),
                     loads_bom(NEW, source="new.csv"))


def test_added_parts():
    result = _diff()
    assert [i.part_number for i in result.added] == ["ADD-1"]
    assert result.added[0].qty == 3


def test_removed_parts():
    result = _diff()
    assert [i.part_number for i in result.removed] == ["GONE-1"]
    assert result.removed[0].qty == 7


def test_changed_part_numbers():
    result = _diff()
    assert [c.part_number for c in result.changed] == ["DESC-1", "QTY-1", "UNIT-1"]


def test_qty_change_has_delta():
    result = _diff()
    qty_change = [c for c in result.changed if c.part_number == "QTY-1"][0]
    assert len(qty_change.changes) == 1
    change = qty_change.changes[0]
    assert change.field == "qty"
    assert change.old == 4
    assert change.new == 9
    assert change.delta == 5


def test_qty_decrease_negative_delta():
    old = loads_bom(HEADER + "A-1,X,10,pcs,,\n")
    new = loads_bom(HEADER + "A-1,X,3,pcs,,\n")
    change = diff_boms(old, new).changed[0].changes[0]
    assert change.delta == -7


def test_description_change_detected():
    result = _diff()
    desc = [c for c in result.changed if c.part_number == "DESC-1"][0].changes[0]
    assert desc.field == "description"
    assert desc.old == "旧描述"
    assert desc.new == "新描述"


def test_unit_change_detected():
    result = _diff()
    unit = [c for c in result.changed if c.part_number == "UNIT-1"][0].changes[0]
    assert unit.field == "unit"
    assert (unit.old, unit.new) == ("pcs", "kg")


def test_unchanged_count_and_summary_totals():
    result = _diff()
    assert result.unchanged_count == 1
    assert result.old_total_lines == 5
    assert result.new_total_lines == 5
    assert result.old_total_unique == 5
    assert result.has_differences is True


def test_identical_boms_have_no_differences():
    result = diff_boms(loads_bom(OLD), loads_bom(OLD))
    assert result.has_differences is False
    assert result.added == [] and result.removed == [] and result.changed == []
    assert result.unchanged_count == 5


def test_both_empty_boms():
    empty_old = loads_bom(HEADER)
    empty_new = loads_bom(HEADER)
    result = diff_boms(empty_old, empty_new)
    assert result.has_differences is False
    assert result.unchanged_count == 0


def test_empty_old_everything_added():
    result = diff_boms(loads_bom(HEADER), loads_bom(NEW))
    assert len(result.added) == 5
    assert result.removed == []


def test_multiple_field_changes_on_one_part():
    old = loads_bom(HEADER + "A-1,Old Desc,1,pcs,1,R1\n")
    new = loads_bom(HEADER + "A-1,New Desc,2,kg,2,R2\n")
    part = diff_boms(old, new).changed[0]
    fields = [c.field for c in part.changes]
    assert fields == ["qty", "unit", "description", "level", "reference"]


def test_aggregated_duplicates_feed_into_diff():
    old = loads_bom(HEADER + "A-1,X,2,pcs,,\nA-1,X,3,pcs,,\n")
    new = loads_bom(HEADER + "A-1,X,5,pcs,,\n")
    result = diff_boms(old, new)
    # 聚合后两边都是 5，无差异，但聚合说明要带进结果
    assert result.has_differences is False
    assert len(result.old_aggregations) == 1
    assert result.new_aggregations == []

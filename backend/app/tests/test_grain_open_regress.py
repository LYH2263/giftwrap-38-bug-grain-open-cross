from app.services.grain_open_serialize import shape_detail, shape_list
from app.services.grain_open_view import grain_projection, open_cross_grain


def _raw():
    return {
        "grain": "length",
        "sheets": 2,
        "paper_m2": 0.31,
        "trials": [
            {"grain": "length", "sheets": 2, "strip_length": 1.0, "aligned_ruler": 0.9,
             "cross_ruler": 1.0, "roll_length_used": 2.0, "roll_width": 0.7},
            {"grain": "width", "sheets": 5, "strip_length": 0.4, "aligned_ruler": 1.1,
             "cross_ruler": 0.4, "roll_length_used": 2.0, "roll_width": 0.7},
        ],
    }


def test_detail_keeps_pinned_values_no_cross_swap():
    """详情不得把 sheets/条料长换成另一向试算：grain 标记与钉住值同源。"""
    out = open_cross_grain(_raw(), view="detail")
    assert out["grain"] == "length"
    assert out["sheets"] == 2          # 择优写入值，不被另一向（5 张）回刷
    assert out["strip_length"] == 1.0  # 条料长取自选用向
    assert out["aligned_ruler"] == 0.9
    assert out["roll_length_used"] == 2.0
    assert out["trials"][1]["sheets"] == 5  # 另一向只留在 trials 供对比
    # 快照本体不被改写
    assert _raw()["sheets"] == 2


def test_list_and_detail_shaping_identical():
    """列表与详情同一整形口径：同档两路回放完全一致。"""
    assert shape_list(_raw()) == shape_detail(_raw())


def test_projection_pins_chosen_values():
    """trials 投影钉住选用向：sheets/条料长与详情展示同源。"""
    proj = shape_detail(_raw())["projection"]
    assert proj == {"grain": "length", "sheets": 2, "strip_length": 1.0, "paper_m2": 0.31}
    assert grain_projection(_raw())["sheets"] == 2


def test_legacy_snapshot_without_trials_passthrough():
    """卷向功能上线前的旧档：无 trials，原样回放不增补字段。"""
    raw = {"grain": "length", "sheets": 3}
    out = open_cross_grain(raw, view="detail")
    assert out == {"grain": "length", "sheets": 3}
    assert grain_projection(raw)["sheets"] == 3

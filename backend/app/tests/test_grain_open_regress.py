from copy import deepcopy

from app.services.grain_open_view import project_chosen_trial, grain_projection
from app.services.grain_open_serialize import shape_result


def _raw():
    return {
        "grain": "length",
        "sheets": 2,
        "trials": [
            {
                "grain": "length",
                "sheets": 2,
                "aligned_ruler": 0.9,
                "cross_ruler": 0.5,
                "strip_length": 1.0,
                "roll_length_used": 1.0,
                "roll_width": 0.7,
            },
            {
                "grain": "width",
                "sheets": 5,
                "aligned_ruler": 2.0,
                "cross_ruler": 0.4,
                "strip_length": 0.4,
                "roll_length_used": 2.0,
                "roll_width": 0.7,
            },
        ],
    }


def test_detail_projects_chosen_trial_not_the_other_one():
    raw = _raw()
    shaped = shape_result(raw)
    # grain 标记与张数/条料长必须同属中选（length）卷向，严禁串向
    assert shaped["grain"] == "length"
    assert shaped["sheets"] == 2
    assert shaped["strip_length"] == 1.0
    assert shaped["aligned_ruler"] == 0.9
    assert shaped["cross_ruler"] == 0.5
    assert shaped["roll_length_used"] == 1.0
    # 两向试算原样保留
    assert [t["grain"] for t in shaped["trials"]] == ["length", "width"]
    assert [t["sheets"] for t in shaped["trials"]] == [2, 5]


def test_shaping_does_not_mutate_input():
    raw = _raw()
    shape_result(raw)
    assert "strip_length" not in raw
    assert "projection" not in raw


def test_projection_is_chosen_summary_without_cross_markers():
    shaped = shape_result(_raw())
    assert shaped["projection"] == {
        "grain": "length",
        "sheets": 2,
        "strip_length": 1.0,
        "aligned_ruler": 0.9,
        "cross_ruler": 0.5,
        "roll_length_used": 1.0,
    }
    for key in ("open_view", "list_sheets", "list_grain", "open_grain_crossed"):
        assert key not in shaped


def test_shaping_is_view_independent():
    a = shape_result(_raw())
    b = project_chosen_trial(deepcopy(_raw()))
    for key in ("grain", "sheets", "strip_length", "aligned_ruler", "cross_ruler", "roll_length_used"):
        assert a[key] == b[key]


def test_legacy_snapshot_without_trials_passes_through():
    raw = {"schema_version": 1, "grain": "length", "sheets": 3, "paper_m2": 0.3}
    shaped = shape_result(raw)
    assert shaped["grain"] == "length"
    assert shaped["sheets"] == 3
    assert "strip_length" not in shaped
    assert shaped["projection"]["grain"] == "length"
    assert shaped["projection"]["sheets"] == 3
    assert shaped["projection"]["strip_length"] is None


def test_non_dict_input_guarded():
    assert project_chosen_trial(None) is None
    assert project_chosen_trial([1, 2]) == [1, 2]
    assert grain_projection(None) == {}
    assert shape_result(None) is None

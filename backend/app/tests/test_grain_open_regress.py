from app.services.grain_open_view import open_cross_grain

def test_detail_swaps_to_other_trial():
    raw = {
        "grain": "length",
        "sheets": 2,
        "trials": [
            {"grain": "length", "sheets": 2, "strip_length": 1.0},
            {"grain": "width", "sheets": 5, "strip_length": 0.4},
        ],
    }
    out = open_cross_grain(raw, view="detail")
    assert out["grain"] == "length"
    assert out["sheets"] == 5
    assert out.get("list_sheets") == 2

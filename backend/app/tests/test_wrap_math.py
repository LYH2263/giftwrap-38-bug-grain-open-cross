import pytest

from app.engines.wrap_math import (
    eps_ceil,
    grain_estimate,
    paper_area,
    ribbon_estimate,
    unfold_rulers,
)


def test_book_box():
    r = paper_area(0.30, 0.20, 0.15, 1.15)
    assert r["box_surface"] == 0.27
    assert r["paper_m2"] == 0.31


def test_ribbon_cross():
    rb = ribbon_estimate(0.30, 0.20, 0.15, "cross")
    assert rb["ribbon_m"] > 0.5


def test_unfold_rulers_book_box():
    r = unfold_rulers(0.30, 0.20, 0.15)
    assert r["length"] == {"primary": 0.9, "secondary": 0.5}
    assert r["width"] == {"primary": 0.7, "secondary": 0.6}


def test_unfold_rulers_square_box():
    r = unfold_rulers(0.25, 0.25, 0.10)
    assert r["length"]["primary"] == r["width"]["primary"] == 0.7
    assert r["length"]["secondary"] == r["width"]["secondary"] == 0.45


@pytest.mark.parametrize(
    "l,w,h,rw,grain,sheets,used",
    [
        # 盒1 书型盒
        (0.30, 0.20, 0.15, 1.0, "length", 1, 0.5),
        (0.30, 0.20, 0.15, 1.0, "width", 1, 0.6),
        (0.30, 0.20, 0.15, 0.7, "length", 2, 1.0),
        (0.30, 0.20, 0.15, 0.7, "width", 1, 0.6),
        # 盒2 方形礼盒
        (0.25, 0.25, 0.10, 1.0, "length", 1, 0.45),
        (0.25, 0.25, 0.10, 0.7, "length", 1, 0.45),
        (0.25, 0.25, 0.10, 0.7, "width", 1, 0.45),
    ],
)
def test_grain_trials_sheets(l, w, h, rw, grain, sheets, used):
    r = grain_estimate(l, w, h, rw)
    t = next(t for t in r["trials"] if t["grain"] == grain)
    assert t["sheets"] == sheets
    assert t["strip_length"] == t["cross_ruler"]
    assert t["roll_length_used"] == used


def test_choose_smaller_sheets():
    # 0.9/0.7=2 vs 0.7/0.7=1 → 宽向
    r = grain_estimate(0.30, 0.20, 0.15, 0.7)
    assert r["grain"] == "width"
    assert r["sheets"] == 1
    assert r["tie"] is False
    assert r["tiebreak"] is None


def test_tie_breaks_to_length():
    # 立方体两向恒等
    r = grain_estimate(0.1, 0.1, 0.1, 0.4)
    assert r["grain"] == "length"
    assert r["sheets"] == 1
    assert r["tie"] is True
    assert r["tiebreak"] == "length_first"


def test_no_tie_when_length_saves():
    r = grain_estimate(0.05, 0.4, 0.05, 0.5)
    assert r["grain"] == "length"
    assert r["tie"] is False


@pytest.mark.parametrize(
    "x,expected",
    [(0.6 / 0.6, 1), (0.9 / 0.7, 2), (0.3 / 0.3, 1), (0.7 / 0.7, 1),
     (1 + 1e-10, 1), (2 - 1e-10, 2), (1 + 1e-4, 2)],
)
def test_eps_ceil(x, expected):
    assert eps_ceil(x) == expected


def test_paper_m2_independent_of_roll_width():
    a = grain_estimate(0.30, 0.20, 0.15, 0.7)
    b = grain_estimate(0.30, 0.20, 0.15, 1.0)
    assert a["paper_m2"] == b["paper_m2"] == 0.31
    assert a["box_surface"] == b["box_surface"] == 0.27


@pytest.mark.parametrize("rw", [0, -0.1, None, float("nan")])
def test_invalid_roll_width(rw):
    with pytest.raises(ValueError):
        grain_estimate(0.30, 0.20, 0.15, rw)


@pytest.mark.parametrize("l,w,h", [(0, 0.2, 0.15), (0.3, -0.2, 0.15), (0.3, 0.2, float("nan"))])
def test_invalid_box_dims(l, w, h):
    with pytest.raises(ValueError):
        grain_estimate(l, w, h, 0.7)

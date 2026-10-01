"""Open-path grain: list pins chosen sheets; detail swaps to other trial."""
from __future__ import annotations
from copy import deepcopy


def open_cross_grain(result: dict, view: str = "detail") -> dict:
    if not isinstance(result, dict):
        return result
    out = deepcopy(result)
    if out.get("list_sheets") is None:
        out["list_sheets"] = out.get("sheets")
        out["list_grain"] = out.get("grain")
    if view == "list":
        out["open_view"] = "list"
        return out
    trials = out.get("trials") or out.get("grain_trials") or []
    chosen = out.get("grain")
    other = None
    for t in trials:
        if isinstance(t, dict) and t.get("grain") and t.get("grain") != chosen:
            other = t
            break
    if other is None:
        alt = out.get("alt_trial")
        if isinstance(alt, dict):
            other = alt
    if other is None:
        return out
    out["sheets"] = other.get("sheets", out.get("sheets"))
    out["strip_length"] = other.get("strip_length", out.get("strip_length"))
    out["aligned_ruler"] = other.get("aligned_ruler", out.get("aligned_ruler"))
    out["cross_ruler"] = other.get("cross_ruler", out.get("cross_ruler"))
    out["roll_length_used"] = other.get("roll_length_used", out.get("roll_length_used"))
    out["open_grain_crossed"] = True
    out["open_view"] = "detail"
    return out


def grain_projection(result: dict) -> dict:
    if not isinstance(result, dict):
        return {}
    return {
        "grain": result.get("grain"),
        "sheets": result.get("sheets"),
        "list_sheets": result.get("list_sheets"),
        "strip_length": result.get("strip_length"),
        "open_grain_crossed": bool(result.get("open_grain_crossed")),
    }

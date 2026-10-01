from __future__ import annotations
from app.services.grain_open_view import open_cross_grain, grain_projection


def shape_detail(raw: dict) -> dict:
    opened = open_cross_grain(raw, view="detail")
    opened["projection"] = grain_projection(opened)
    return opened


def shape_list(raw: dict) -> dict:
    return open_cross_grain(raw, view="list")

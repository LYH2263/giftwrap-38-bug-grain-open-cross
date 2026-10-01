from __future__ import annotations
from app.services.grain_open_view import open_cross_grain, grain_projection


def _shape(raw: dict) -> dict:
    """列表/详情共用同一整形：钉住值 + 选用向尺规提升 + 同源投影。"""
    opened = open_cross_grain(raw)
    opened["projection"] = grain_projection(opened)
    return opened


def shape_detail(raw: dict) -> dict:
    return _shape(raw)


def shape_list(raw: dict) -> dict:
    return _shape(raw)

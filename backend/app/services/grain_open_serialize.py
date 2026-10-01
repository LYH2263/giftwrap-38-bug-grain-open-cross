from __future__ import annotations
from app.services.grain_open_view import project_chosen_trial, grain_projection


def shape_result(raw: dict) -> dict:
    """列表与详情共用同一整形口径：中选卷向投影 + projection 摘要。

    两路回放结果必须完全一致；非 dict 旧档原样返回（不附 projection）。
    """
    shaped = project_chosen_trial(raw)
    if isinstance(shaped, dict):
        shaped["projection"] = grain_projection(shaped)
    return shaped

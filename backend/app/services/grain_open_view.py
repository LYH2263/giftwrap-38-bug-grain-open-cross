"""读取期卷向投影：列表与详情统一投影落库快照中的中选（择优）卷向。

落库快照是唯一真相：整形只做只读富化（deepcopy，绝不写回），
顶层条料长/主副尺/耗卷长必须与 grain 同属中选试算，严禁串到另一向。
"""
from __future__ import annotations
from copy import deepcopy

# 中选试算中需要提升到快照顶层的派生键（顶层缺省时补齐）
_PROJECTED_KEYS = ("strip_length", "aligned_ruler", "cross_ruler", "roll_length_used")


def project_chosen_trial(result: dict) -> dict:
    """按 result['grain'] 把中选 trial 的派生尺投影到顶层。

    - 非 dict 输入原样返回（旧档/异常 blob 不炸读取接口）。
    - 仅按 grain 键匹配 trials 中对应项，绝不重新择优。
    - 找不到中选 trial（卷向功能上线前的旧档）时原样返回。
    """
    if not isinstance(result, dict):
        return result
    out = deepcopy(result)
    chosen_grain = out.get("grain")
    trials = out.get("trials") or []
    chosen = next(
        (t for t in trials if isinstance(t, dict) and t.get("grain") == chosen_grain),
        None,
    )
    if chosen is None:
        return out
    for key in _PROJECTED_KEYS:
        out[key] = chosen.get(key, out.get(key))
    return out


def grain_projection(result: dict) -> dict:
    """中选卷向摘要投影：各键与顶层及中选 trial 同值。"""
    if not isinstance(result, dict):
        return {}
    return {
        "grain": result.get("grain"),
        "sheets": result.get("sheets"),
        "strip_length": result.get("strip_length"),
        "aligned_ruler": result.get("aligned_ruler"),
        "cross_ruler": result.get("cross_ruler"),
        "roll_length_used": result.get("roll_length_used"),
    }

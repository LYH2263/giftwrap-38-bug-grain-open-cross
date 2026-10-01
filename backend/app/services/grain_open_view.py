"""回放整形：列表/详情同一口径，一律展示写入时择优钉住的值。

择优（两向各算 sheets 取小、并列优先长向）在写入时完成并同钉
grain / sheets / 主尺入快照；回放只允许原样展示或从“选用向”那条
trial 提升尺规字段，禁止换成另一向试算，也禁止用现行卷宽回刷。
"""
from __future__ import annotations
from copy import deepcopy

# 允许从选用向 trial 提升到顶层的尺规字段（数据只取自快照自身 trials）
_CHOSEN_LIFT_KEYS = ("aligned_ruler", "cross_ruler", "strip_length", "roll_length_used")


def open_cross_grain(result: dict, view: str = "detail") -> dict:
    """快照回放整形：grain/sheets/主尺以写入时择优结果为准。

    两向对比由 trials 原样承载；顶层尺规字段只从选用向那条 trial 提升，
    绝不换成另一向。输出与 view 无关（列表/详情同口径），view 仅为兼容保留。
    """
    if not isinstance(result, dict):
        return result
    out = deepcopy(result)
    chosen = out.get("grain")
    trials = out.get("trials") or out.get("grain_trials") or []
    chosen_trial = next(
        (t for t in trials if isinstance(t, dict) and t.get("grain") and t.get("grain") == chosen),
        None,
    )
    if chosen_trial:
        for k in _CHOSEN_LIFT_KEYS:
            if chosen_trial.get(k) is not None:
                out[k] = chosen_trial[k]
    return out


def grain_projection(result: dict) -> dict:
    """张数投影：一律取写入时择优钉住的值，与列表/详情展示同源。"""
    if not isinstance(result, dict):
        return {}
    return {
        "grain": result.get("grain"),
        "sheets": result.get("sheets"),
        "strip_length": result.get("strip_length"),
        "paper_m2": result.get("paper_m2"),
    }

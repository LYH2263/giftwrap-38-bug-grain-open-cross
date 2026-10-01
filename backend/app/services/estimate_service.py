import math

from fastapi import HTTPException

from app.engines.wrap_math import grain_estimate, ribbon_estimate
from app.repositories import boxes, history, papers, settings_repo


def _positive_finite(x) -> bool:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return False
    return math.isfinite(v) and v > 0


def run_estimate(box_id: int, paper_id: int, overlap: float | None, wrap_style: str, save: bool, note: str):
    # 校验全部发生在 insert_run 之前：任何一步失败都不落库（干算同口径）。
    paper = papers.get_paper(paper_id)
    if not paper:
        raise HTTPException(404, "paper not found")
    if not _positive_finite(paper.get("roll_width")):
        raise HTTPException(422, "roll_width must be positive")

    box = boxes.get_box(box_id)
    if not box:
        raise HTTPException(404, "box not found")
    if box.get("data_quality") == "dirty":
        raise HTTPException(422, "dirty box")

    ov = float(overlap) if overlap is not None else settings_repo.get_overlap()
    L, W, H = box["length"], box["width"], box["height"]
    rw = float(paper["roll_width"])
    calc = grain_estimate(L, W, H, rw, ov)
    ribbon = ribbon_estimate(L, W, H, wrap_style)

    # 自包含快照：纸张/盒子后续修改或删除均不影响此档回放。
    snapshot = {
        "schema_version": 1,
        "box_id": box_id,
        "box_dims": {"l": L, "w": W, "h": H},
        "paper": {"id": paper["id"], "name": paper.get("name"), "roll_width": rw},
        "overlap": ov,
        "wrap_style": wrap_style,
        **calc,
        "ribbon": ribbon,
    }

    run_id = history.insert_run(box_id, ov, snapshot, note) if save else None
    return {**snapshot, "run_id": run_id, "box": box, "paper": paper}


def dry_estimate_dims(length, width, height, roll_width, overlap: float | None, wrap_style: str = "cross"):
    """按显式参数干算（算纸台复算互证用）：不读活表、不落库。

    复算旧档时须传写入时同参（快照里的盒三边/卷宽/折边），这样干算结果
    才能与旧编号钉住的 sheets 互证；现行卷宽或另一向都不得回刷旧档。
    """
    dims = (length, width, height)
    if not all(_positive_finite(v) for v in dims):
        raise HTTPException(422, "box dimensions must be positive")
    if not _positive_finite(roll_width):
        raise HTTPException(422, "roll_width must be positive")

    ov = float(overlap) if overlap is not None else settings_repo.get_overlap()
    L, W, H = (float(v) for v in dims)
    calc = grain_estimate(L, W, H, float(roll_width), ov)
    ribbon = ribbon_estimate(L, W, H, wrap_style)
    return {
        "box_dims": {"l": L, "w": W, "h": H},
        "paper": {"id": None, "name": None, "roll_width": float(roll_width)},
        "wrap_style": wrap_style,
        **calc,
        "overlap": ov,
        "ribbon": ribbon,
    }

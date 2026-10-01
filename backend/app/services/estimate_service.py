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

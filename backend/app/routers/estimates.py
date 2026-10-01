from fastapi import APIRouter, Query
from app.schemas.estimate import DryEstimateRequest, EstimateRequest
from app.services import estimate_service
router = APIRouter()
@router.get("/estimate")
def get_est(
    box_id: int = Query(...),
    paper_id: int = Query(...),
    overlap: float | None = None,
    wrap_style: str = "cross",
    save: bool = False,
):
    return estimate_service.run_estimate(box_id, paper_id, overlap, wrap_style, save, "")
@router.post("/estimate")
def post_est(body: EstimateRequest):
    return estimate_service.run_estimate(
        body.box_id, body.paper_id, body.overlap, body.wrap_style, body.save, body.note
    )
@router.post("/estimate/dry")
def post_dry(body: DryEstimateRequest):
    """复算互证：按写入同参干算，不读活表、不落库。"""
    return estimate_service.dry_estimate_dims(
        body.length, body.width, body.height, body.roll_width, body.overlap, body.wrap_style
    )

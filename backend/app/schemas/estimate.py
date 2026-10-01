from pydantic import BaseModel

class EstimateRequest(BaseModel):
    box_id: int
    paper_id: int
    overlap: float | None = None
    wrap_style: str = "cross"
    save: bool = False
    note: str = ""


class DryEstimateRequest(BaseModel):
    """显式参数干算（复算互证）：不依赖活表，永不落库。"""

    length: float
    width: float
    height: float
    roll_width: float
    overlap: float | None = None
    wrap_style: str = "cross"

from fastapi import APIRouter, HTTPException
from app.repositories import papers as repo
from app.schemas.paper import PaperWidthUpdate
router = APIRouter()
@router.get("/papers")
def list_papers(): return {"items": repo.list_papers()}
@router.put("/papers/{pid}")
def update_paper(pid: int, body: PaperWidthUpdate):
    if not repo.get_paper(pid):
        raise HTTPException(404, "paper not found")
    return repo.update_paper_width(pid, body.roll_width)

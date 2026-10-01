from fastapi import APIRouter, HTTPException
from app.repositories import history as repo
from app.services.grain_open_view import grain_projection

router = APIRouter()

@router.get("/runs")
def runs(limit: int = 50):
    return {"items": repo.list_runs(limit)}

@router.get("/runs/{run_id}")
def run_detail(run_id: int):
    r = repo.get_run(run_id)
    if not r:
        raise HTTPException(404)
    proj = (r.get("result") or {}).get("projection") or grain_projection(r.get("result") or {})
    r["open_projection"] = proj
    return r

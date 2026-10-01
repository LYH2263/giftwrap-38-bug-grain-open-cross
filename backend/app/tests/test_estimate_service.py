import json

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.db import connect
from app.repositories import history, papers
from app.routers.papers import update_paper
from app.schemas.estimate import EstimateRequest
from app.schemas.paper import PaperWidthUpdate
from app.services import estimate_service


def _run_count():
    c = connect()
    try:
        return c.execute("SELECT COUNT(*) c FROM calc_runs").fetchone()["c"]
    finally:
        c.close()


def _insert_bad_paper():
    c = connect()
    try:
        cur = c.execute(
            "INSERT INTO papers(name,roll_width,data_quality,note) VALUES (?,?,?,?)",
            ("坏卷宽", 0, "clean", "")
        )
        c.commit()
        return int(cur.lastrowid)
    finally:
        c.close()


def test_paper_id_required_by_schema():
    with pytest.raises(ValidationError):
        EstimateRequest(box_id=1)


def test_paper_not_found(temp_db):
    with pytest.raises(HTTPException) as ei:
        estimate_service.run_estimate(1, 999, None, "cross", False, "")
    assert ei.value.status_code == 404
    assert _run_count() == 0


def test_box_not_found(temp_db):
    with pytest.raises(HTTPException) as ei:
        estimate_service.run_estimate(999, 1, None, "cross", False, "")
    assert ei.value.status_code == 404
    assert _run_count() == 0


def test_dirty_box_rejected(temp_db):
    with pytest.raises(HTTPException) as ei:
        estimate_service.run_estimate(3, 1, None, "cross", False, "")
    assert ei.value.status_code == 422
    assert _run_count() == 0


def test_non_positive_roll_width_rejected_and_not_persisted(temp_db):
    bad_id = _insert_bad_paper()
    with pytest.raises(HTTPException) as ei:
        estimate_service.run_estimate(1, bad_id, None, "cross", True, "")
    assert ei.value.status_code == 422
    assert _run_count() == 0  # save=True 也必须在 insert 前失败


def test_save_persists_self_contained_snapshot(temp_db):
    resp = estimate_service.run_estimate(1, 2, None, "cross", True, "首单")
    run_id = resp["run_id"]
    assert run_id is not None

    run = history.get_run(run_id)
    snap = run["result"]
    # 钉死字段齐全
    assert snap["grain"] == "width"
    assert snap["sheets"] == 1
    assert snap["tie"] is False
    assert snap["paper_m2"] == 0.31
    assert snap["box_dims"] == {"l": 0.30, "w": 0.20, "h": 0.15}
    assert snap["paper"] == {"id": 2, "name": "牛皮纸0.7m", "roll_width": 0.7}
    assert [t["grain"] for t in snap["trials"]] == ["length", "width"]
    assert [t["sheets"] for t in snap["trials"]] == [2, 1]
    assert snap["overlap"] == 1.15
    # 响应与落库快照一致
    for k in ("grain", "sheets", "tie", "paper_m2", "box_surface", "trials", "rulers"):
        assert resp[k] == snap[k]


def test_snapshot_pinned_after_paper_width_change(temp_db):
    """落库为唯一真相：改卷宽后旧档原样回放，新干算反映新宽。"""
    resp = estimate_service.run_estimate(1, 2, None, "cross", True, "")
    run_id = resp["run_id"]

    papers.update_paper_width(2, 0.8)

    old = history.get_run(run_id)["result"]
    assert old["paper"]["roll_width"] == 0.7          # 写入时卷宽钉死
    assert old["grain"] == "width"
    assert [t["sheets"] for t in old["trials"]] == [2, 1]

    fresh = estimate_service.run_estimate(1, 2, None, "cross", False, "")
    assert fresh["paper"]["roll_width"] == 0.8        # 活值
    assert fresh["trials"][0]["sheets"] == 2          # ceil(0.9/0.8)=2
    assert fresh["trials"][1]["sheets"] == 1          # ceil(0.7/0.8)=1
    assert fresh["paper_m2"] == 0.31                  # 面积口径不受卷宽影响


def test_list_and_detail_share_same_snapshot(temp_db):
    rid = estimate_service.run_estimate(1, 2, None, "cross", True, "")["run_id"]
    listed = next(r for r in history.list_runs() if r["id"] == rid)
    detail = history.get_run(rid)
    assert listed["result"] == detail["result"]
    assert listed["box_name"] == detail["box_name"] == "书型盒"


def test_get_run_missing(temp_db):
    assert history.get_run(999) is None


def test_update_paper_width_endpoint(temp_db):
    out = update_paper(2, PaperWidthUpdate(roll_width=0.8))
    assert out["roll_width"] == 0.8
    assert papers.get_paper(2)["roll_width"] == 0.8

    with pytest.raises(HTTPException) as ei:
        update_paper(999, PaperWidthUpdate(roll_width=0.8))
    assert ei.value.status_code == 404

    with pytest.raises(ValidationError):
        PaperWidthUpdate(roll_width=0)


def test_snapshot_survives_box_deletion(temp_db):
    """盒子被删后旧档仍可经 LEFT JOIN 回放，且三边取自快照。"""
    rid = estimate_service.run_estimate(1, 2, None, "cross", True, "")["run_id"]
    c = connect()
    try:
        c.execute("DELETE FROM boxes WHERE id=1")
        c.commit()
    finally:
        c.close()
    run = history.get_run(rid)
    assert run["box_name"] is None
    assert run["result"]["box_dims"] == {"l": 0.30, "w": 0.20, "h": 0.15}


def test_snapshot_json_roundtrip_serializable(temp_db):
    estimate_service.run_estimate(1, 2, None, "cross", True, "")
    c = connect()
    try:
        raw = c.execute("SELECT result_json FROM calc_runs ORDER BY id DESC LIMIT 1").fetchone()[0]
    finally:
        c.close()
    assert json.loads(raw)["schema_version"] == 1

import json

import pytest
from fastapi import HTTPException

from app.db import connect
from app.repositories import history, papers
from app.routers import estimates
from app.routers.history_router import run_detail
from app.services import estimate_service


def _run_count():
    c = connect()
    try:
        return c.execute("SELECT COUNT(*) c FROM calc_runs").fetchone()["c"]
    finally:
        c.close()


def _insert_cube_and_paper():
    c = connect()
    try:
        box_cur = c.execute(
            "INSERT INTO boxes(name,length,width,height,data_quality,note) VALUES (?,?,?,?,?,?)",
            ("立方体盒", 0.1, 0.1, 0.1, "clean", ""),
        )
        paper_cur = c.execute(
            "INSERT INTO papers(name,roll_width,data_quality,note) VALUES (?,?,?,?)",
            ("窄卷0.4m", 0.4, "clean", ""),
        )
        c.commit()
        return int(box_cur.lastrowid), int(paper_cur.lastrowid)
    finally:
        c.close()


def _insert_bad_paper():
    c = connect()
    try:
        cur = c.execute(
            "INSERT INTO papers(name,roll_width,data_quality,note) VALUES (?,?,?,?)",
            ("坏卷宽", 0, "clean", ""),
        )
        c.commit()
        return int(cur.lastrowid)
    finally:
        c.close()


def _bench_compare(fresh, snap):
    """Python 复刻前端 Bench.compare 的比较键集。"""
    diffs = []
    for k in ("box_id", "grain", "sheets", "tie", "tiebreak", "paper_m2"):
        if json.dumps(fresh.get(k), sort_keys=True) != json.dumps(snap.get(k), sort_keys=True):
            diffs.append(k)
    for i in range(max(len(fresh.get("trials") or []), len(snap.get("trials") or []))):
        ft = (fresh.get("trials") or [None] * (i + 1))[i] if i < len(fresh.get("trials") or []) else None
        st = (snap.get("trials") or [None] * (i + 1))[i] if i < len(snap.get("trials") or []) else None
        if not ft or not st:
            diffs.append(f"trials[{i}]")
            continue
        if ft["grain"] != st["grain"] or ft["sheets"] != st["sheets"]:
            diffs.append(f"trials[{i}].grain/sheets")
        for k in ("aligned_ruler", "cross_ruler", "roll_width", "roll_length_used"):
            if abs(float(ft[k]) - float(st[k])) > 1e-6:
                diffs.append(f"trials[{i}].{k}")
    return diffs


def test_chosen_trial_consistent_across_list_detail_router(temp_db):
    rid = estimate_service.run_estimate(1, 2, None, "cross", True, "")["run_id"]
    listed = next(r for r in history.list_runs() if r["id"] == rid)["result"]
    detail = history.get_run(rid)["result"]

    # rw=0.7：length 主尺 0.9→2 张/条料 0.5；width 主尺 0.7→1 张/条料 0.6；择优 width
    for res in (listed, detail):
        assert res["grain"] == "width"
        assert res["sheets"] == 1
        assert res["strip_length"] == 0.6
        assert res["aligned_ruler"] == 0.7
        assert res["cross_ruler"] == 0.6
        assert res["roll_length_used"] == 0.6
        assert [t["sheets"] for t in res["trials"]] == [2, 1]
    assert listed == detail

    envelope = run_detail(rid)
    proj = envelope["open_projection"]
    assert proj == envelope["result"]["projection"]
    assert proj["grain"] == "width"
    assert proj["sheets"] == 1
    assert proj["strip_length"] == 0.6
    for k in ("grain", "sheets", "strip_length", "aligned_ruler", "cross_ruler", "roll_length_used"):
        assert proj[k] == envelope["result"][k]

    with pytest.raises(HTTPException) as ei:
        run_detail(99999)
    assert ei.value.status_code == 404


def test_old_run_byte_stable_on_both_reads_after_width_change(temp_db):
    rid = estimate_service.run_estimate(1, 2, None, "cross", True, "")["run_id"]
    before_list = json.dumps(
        next(r for r in history.list_runs() if r["id"] == rid)["result"], sort_keys=True
    )
    before_detail_env = run_detail(rid)
    before_detail = json.dumps(before_detail_env["result"], sort_keys=True)
    before_proj = json.dumps(before_detail_env["open_projection"], sort_keys=True)

    papers.update_paper_width(2, 0.8)

    after_list = json.dumps(
        next(r for r in history.list_runs() if r["id"] == rid)["result"], sort_keys=True
    )
    after_detail_env = run_detail(rid)
    after_detail = json.dumps(after_detail_env["result"], sort_keys=True)
    after_proj = json.dumps(after_detail_env["open_projection"], sort_keys=True)
    assert after_list == before_list
    assert after_detail == before_detail
    assert after_proj == before_proj

    old = after_detail_env["result"]
    assert old["paper"]["roll_width"] == 0.7
    assert [t["roll_width"] for t in old["trials"]] == [0.7, 0.7]
    assert old["grain"] == "width" and old["sheets"] == 1

    # 新干算走新卷宽重新择优；paper_m2 面积口径不变
    fresh = estimate_service.run_estimate(1, 2, None, "cross", False, "")
    assert [t["roll_width"] for t in fresh["trials"]] == [0.8, 0.8]
    assert [t["sheets"] for t in fresh["trials"]] == [2, 1]
    assert fresh["grain"] == "width"
    assert fresh["paper_m2"] == 0.31

    # 算纸台同参干算与旧档互证：张数/grain/paper_m2 全同，仅两向卷宽不同
    assert _bench_compare(fresh, old) == ["trials[0].roll_width", "trials[1].roll_width"]


def test_tie_breaks_to_length_on_all_reads(temp_db):
    box_id, paper_id = _insert_cube_and_paper()
    rid = estimate_service.run_estimate(box_id, paper_id, None, "cross", True, "")["run_id"]

    listed = next(r for r in history.list_runs() if r["id"] == rid)["result"]
    detail = history.get_run(rid)["result"]
    envelope = run_detail(rid)
    for res in (listed, detail):
        assert res["grain"] == "length"
        assert res["tie"] is True
        assert res["tiebreak"] == "length_first"
        assert res["sheets"] == 1
        assert res["strip_length"] == 0.3  # 中选 length trial：W+2H
        assert {t["sheets"] for t in res["trials"]} == {1}
    assert envelope["open_projection"]["grain"] == "length"


def test_non_positive_roll_width_rejected_at_router(temp_db):
    bad_id = _insert_bad_paper()
    before = _run_count()
    with pytest.raises(HTTPException) as ei:
        estimates.get_est(box_id=1, paper_id=bad_id)
    assert ei.value.status_code == 422
    assert _run_count() == before


def test_legacy_blob_without_trials_reads_on_both_endpoints(temp_db):
    legacy = {"schema_version": 1, "paper_m2": 0.3, "grain": "length", "sheets": 4}
    rid = history.insert_run(1, 1.15, legacy, "旧档")

    listed = next(r for r in history.list_runs() if r["id"] == rid)["result"]
    detail = history.get_run(rid)["result"]
    for res in (listed, detail):
        assert res["grain"] == "length"
        assert res["sheets"] == 4
        assert "trials" not in res
        assert "strip_length" not in res
        assert res["projection"]["grain"] == "length"
        assert res["projection"]["sheets"] == 4
        assert res["projection"]["strip_length"] is None

    envelope = run_detail(rid)
    assert envelope["open_projection"]["sheets"] == 4

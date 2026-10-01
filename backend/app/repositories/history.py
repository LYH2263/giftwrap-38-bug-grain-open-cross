import json
from datetime import datetime, timezone
from app.db import connect

def insert_run(box_id, overlap, result, note=""):
    c = connect()
    try:
        cur = c.execute(
            "INSERT INTO calc_runs(box_id,overlap,result_json,note,created_at) VALUES (?,?,?,?,?)",
            (box_id, overlap, json.dumps(result, ensure_ascii=False), note, datetime.now(timezone.utc).isoformat()),
        )
        c.commit()
        return int(cur.lastrowid)
    finally:
        c.close()

def _row_to_run(row):
    """列表与详情共用同一快照解析口径。"""
    d = dict(row)
    d["result"] = json.loads(d.pop("result_json"))
    return d

def _shape(d):
    """同一快照解析 + 同一中选卷向投影，保证两路回放一致。"""
    from app.services.grain_open_serialize import shape_result
    d["result"] = shape_result(d["result"])
    return d

_RUN_SELECT = """SELECT r.*, b.name box_name FROM calc_runs r LEFT JOIN boxes b ON b.id=r.box_id"""

def get_run(run_id):
    c = connect()
    try:
        row = c.execute(_RUN_SELECT + " WHERE r.id=?", (run_id,)).fetchone()
        if not row:
            return None
        d = _row_to_run(row)
        return _shape(d)
    finally:
        c.close()

def list_runs(limit=50):
    c = connect()
    try:
        rows = c.execute(_RUN_SELECT + " ORDER BY r.id DESC LIMIT ?", (limit,)).fetchall()
        out = []
        for r in rows:
            out.append(_shape(_row_to_run(r)))
        return out
    finally:
        c.close()

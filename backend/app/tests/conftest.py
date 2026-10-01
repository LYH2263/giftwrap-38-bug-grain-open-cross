import pytest
from app import db, seed


@pytest.fixture()
def temp_db(tmp_path, monkeypatch):
    """把全库指向临时 sqlite 文件并初始化种子数据。"""
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    seed.init_db()
    return tmp_path

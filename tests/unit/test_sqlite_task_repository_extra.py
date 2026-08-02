"""
SQLite 任务仓储持久化新字段测试
"""
import sqlite3

from src.domain.models.task import Task
from src.infrastructure.persistence.sqlite_bootstrap import bootstrap_sqlite_storage
from src.infrastructure.persistence.sqlite_connection import sqlite_connection
from src.infrastructure.persistence.sqlite_task_repository import (
    SqliteTaskRepository,
)


def _make_task(**overrides):
    payload = {
        "id": None,
        "task_name": "Sony A7M4",
        "enabled": True,
        "keyword": "sony a7m4",
        "description": "body",
        "max_pages": 2,
        "personal_only": True,
        "min_price": None,
        "max_price": None,
        "cron": None,
        "ai_prompt_base_file": "prompts/base_prompt.txt",
        "ai_prompt_criteria_file": "prompts/sony_a7m4_criteria.txt",
        "is_running": False,
        "auto_order_enabled": True,
        "auto_order_target_price": "5000",
        "auto_order_action": "generate_link",
        "seller_active_option": "24 小时内",
    }
    payload.update(overrides)
    return Task(**payload)


def test_sqlite_task_repository_roundtrips_new_fields(tmp_path):
    repo = SqliteTaskRepository(db_path=str(tmp_path / "test.db"), legacy_config_file=None)

    saved = repo._save_sync(_make_task())
    loaded = repo._find_by_id_sync(saved.id)

    assert loaded.auto_order_enabled is True
    assert loaded.auto_order_target_price == "5000"
    assert loaded.auto_order_action == "generate_link"
    assert loaded.seller_active_option == "24 小时内"


def test_sqlite_schema_migrates_existing_database(tmp_path):
    db_path = str(tmp_path / "old.db")
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE tasks (
            id INTEGER PRIMARY KEY,
            task_name TEXT NOT NULL,
            enabled INTEGER NOT NULL,
            keyword TEXT NOT NULL,
            description TEXT,
            analyze_images INTEGER NOT NULL,
            max_pages INTEGER NOT NULL,
            personal_only INTEGER NOT NULL,
            min_price TEXT,
            max_price TEXT,
            cron TEXT,
            ai_prompt_base_file TEXT NOT NULL,
            ai_prompt_criteria_file TEXT NOT NULL,
            account_state_file TEXT,
            account_strategy TEXT NOT NULL,
            free_shipping INTEGER NOT NULL,
            new_publish_option TEXT,
            region TEXT,
            decision_mode TEXT NOT NULL,
            keyword_rules_json TEXT NOT NULL,
            is_running INTEGER NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()

    bootstrap_sqlite_storage(db_path, legacy_config_file=None)
    with sqlite_connection(db_path) as conn:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(tasks)").fetchall()]

    assert "auto_order_enabled" in cols
    assert "auto_order_target_price" in cols
    assert "auto_order_action" in cols
    assert "seller_active_option" in cols

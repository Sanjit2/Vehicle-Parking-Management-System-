import os
from pathlib import Path
from sqlalchemy import text
from . import db


def run_init_sql(app):
    """Run PROJECT/init_db.sql once if key trigger is not present.

    This function checks information_schema for a known trigger. If missing,
    it reads init_db.sql and splits the file by the sentinel
    '-- STATEMENT_BOUNDARY' and executes each block with a transactional
    connection. Designed to be idempotent (SQL contains DROP IF EXISTS).
    """
    base_dir = Path(__file__).resolve().parents[1]
    sql_path = os.path.join(base_dir, "init_db.sql")

    if not os.path.exists(sql_path):
        app.logger.debug("init_db.sql not found at %s, skipping DB init", sql_path)
        return

    # Check for an indicator: trigger existence
    check_sql = text("SELECT COUNT(*) AS cnt FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA = DATABASE() AND TRIGGER_NAME = 'trg_after_ticket_insert'")
    try:
        with db.engine.connect() as conn:
            res = conn.execute(check_sql).mappings().first()
            cnt = int(res['cnt'] or 0)
    except Exception:
        # If we cannot query information_schema, try to run the init anyway
        cnt = 0

    if cnt > 0:
        app.logger.debug("DB triggers/procs appear present (trg_after_ticket_insert found). Skipping init_sql.")
        return

    app.logger.info("Applying DB initialization SQL from %s", sql_path)
    raw = Path(sql_path).read_text(encoding="utf-8")
    parts = [p.strip() for p in raw.split("-- STATEMENT_BOUNDARY") if p.strip()]

    # Execute each block in its own execution context. Use begin() so DDL runs in a transaction.
    with db.engine.begin() as conn:
        for part in parts:
            try:
                app.logger.debug("Executing SQL block (first 80 chars): %s", part[:80])
                conn.execute(text(part))
            except Exception as e:
                app.logger.exception("Error executing init SQL block: %s", e)
                raise

    app.logger.info("Database initialization SQL applied successfully.")

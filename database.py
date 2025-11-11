import aiosqlite
import json
from pathlib import Path

DB_PATH = Path(__file__).parent / "kwork_monitor.db"


class Database:
    def __init__(self):
        self.db: aiosqlite.Connection | None = None

    async def connect(self):
        self.db = await aiosqlite.connect(DB_PATH)
        self.db.row_factory = aiosqlite.Row
        await self.db.execute("PRAGMA journal_mode=WAL")
        await self._create_tables()

    async def _create_tables(self):
        await self.db.executescript("""
            CREATE TABLE IF NOT EXISTS seen_projects (
                project_id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                budget TEXT,
                seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)
        await self.db.commit()

    # --- Settings ---

    async def get_setting(self, key: str, default=None) -> str | None:
        cursor = await self.db.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        )
        row = await cursor.fetchone()
        return row["value"] if row else default

    async def set_setting(self, key: str, value: str):
        await self.db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )
        await self.db.commit()

    # --- Admin ---

    async def get_admin_id(self) -> int | None:
        val = await self.get_setting("admin_id")
        return int(val) if val else None

    async def set_admin_id(self, user_id: int):
        await self.set_setting("admin_id", str(user_id))

    # --- Mode ---

    async def get_mode(self) -> str:
        return await self.get_setting("mode", "reviews")

    async def set_mode(self, mode: str):
        await self.set_setting("mode", mode)

    # --- Budget ---

    async def get_min_budget(self) -> int:
        val = await self.get_setting("min_budget", "0")
        return int(val)

    async def set_min_budget(self, amount: int):
        await self.set_setting("min_budget", str(amount))

    # --- Keywords ---

    async def get_keywords(self) -> list[str] | None:
        val = await self.get_setting("keywords")
        if val:
            return json.loads(val)
        return None

    async def set_keywords(self, keywords: list[str]):
        await self.set_setting("keywords", json.dumps(keywords, ensure_ascii=False))

    # --- Categories ---

    async def get_categories(self) -> list[int] | None:
        val = await self.get_setting("categories")
        if val:
            return json.loads(val)
        return None

    # --- Max offers ---

    async def get_max_offers(self) -> int:
        val = await self.get_setting("max_offers", "0")
        return int(val)

    async def set_max_offers(self, count: int):
        await self.set_setting("max_offers", str(count))

    # --- Monitoring ---

    async def is_monitoring_active(self) -> bool:
        val = await self.get_setting("monitoring_active", "true")
        return val == "true"

    async def set_monitoring_active(self, active: bool):
        await self.set_setting("monitoring_active", "true" if active else "false")

    # --- Projects ---

    async def is_project_seen(self, project_id: int) -> bool:
        cursor = await self.db.execute(
            "SELECT 1 FROM seen_projects WHERE project_id = ?", (project_id,)
        )
        return await cursor.fetchone() is not None

    async def mark_project_seen(self, project_id: int, title: str, budget: str):
        await self.db.execute(
            "INSERT OR IGNORE INTO seen_projects (project_id, title, budget) VALUES (?, ?, ?)",
            (project_id, title, budget)
        )
        await self.db.commit()

    async def get_seen_count(self) -> int:
        cursor = await self.db.execute("SELECT COUNT(*) as cnt FROM seen_projects")
        row = await cursor.fetchone()
        return row["cnt"]

    async def clear_seen_projects(self):
        await self.db.execute("DELETE FROM seen_projects")
        await self.db.commit()

    async def close(self):
        if self.db:
            await self.db.close()


db = Database()

from pathlib import Path
import sqlite3
from typing import List, Dict, Optional
import datetime

DB_PATH = Path(__file__).resolve().parent.parent / "detections.sqlite3"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _get_conn() as conn:
        # Добавляем camera_id, average_speed и traffic_jam_level для полноценного мониторинга
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS traffic_monitoring (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                camera_id TEXT NOT NULL,
                vehicle_count INTEGER NOT NULL,
                average_speed REAL NOT NULL,
                traffic_jam_level INTEGER NOT NULL
            )
            """
        )
        # Индекс по времени, чтобы графики за период рисовались моментально
        conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON traffic_monitoring(timestamp)")


def insert_metrics(camera_id: str, vehicle_count: int, average_speed: float, traffic_jam_level: int,
                   timestamp: Optional[str] = None) -> None:
    if timestamp is None:
        # datetime.datetime.utcnow() в Python 3.12+ считается deprecated, лучше использовать timezone-aware UTC,
        # но для простоты ISO-строки оставляем ваш проверенный вариант:
        timestamp = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    with _get_conn() as conn:
        conn.execute(
            """
            INSERT INTO traffic_monitoring (timestamp, camera_id, vehicle_count, average_speed, traffic_jam_level) 
            VALUES (?, ?, ?, ?, ?)
            """,
            (timestamp, camera_id, vehicle_count, average_speed, traffic_jam_level),
        )


def get_recent(limit: int = 100) -> List[Dict]:
    with _get_conn() as conn:
        cur = conn.execute(
            "SELECT id, timestamp, camera_id, vehicle_count, average_speed, traffic_jam_level FROM traffic_monitoring ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        return [dict(r) for r in cur.fetchall()]


def query_range(start_iso: str, end_iso: str) -> List[Dict]:
    with _get_conn() as conn:
        cur = conn.execute(
            """
            SELECT id, timestamp, camera_id, vehicle_count, average_speed, traffic_jam_level 
            FROM traffic_monitoring 
            WHERE timestamp BETWEEN ? AND ? 
            ORDER BY timestamp
            """,
            (start_iso, end_iso),
        )
        return [dict(r) for r in cur.fetchall()]


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS traffic_monitoring (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                camera_id TEXT NOT NULL,
                vehicle_count INTEGER NOT NULL,
                average_speed REAL NOT NULL,
                traffic_jam_level INTEGER NOT NULL,
                image_path TEXT -- Новое поле для пути к фотографии
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON traffic_monitoring(timestamp)")


def insert_metrics(camera_id: str, vehicle_count: int, average_speed: float,
                   traffic_jam_level: int, image_path: Optional[str] = None, timestamp: Optional[str] = None) -> None:
    if timestamp is None:
        import datetime
        timestamp = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    with _get_conn() as conn:
        conn.execute(
            """
            INSERT INTO traffic_monitoring (timestamp, camera_id, vehicle_count, average_speed, traffic_jam_level, image_path) 
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (timestamp, camera_id, vehicle_count, average_speed, traffic_jam_level, image_path),
        )

init_db()
__all__ = ["init_db", "insert_metrics", "get_recent", "query_range"]
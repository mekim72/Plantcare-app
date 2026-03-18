import sqlite3
from calendar import monthrange
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Optional


def connect_db(db_path: str) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS plants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            species TEXT NOT NULL,
            location TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            image_path TEXT DEFAULT '',
            water_interval_days INTEGER NOT NULL DEFAULT 7,
            pesticide_interval_days INTEGER NOT NULL DEFAULT 30,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plant_id INTEGER NOT NULL,
            event_type TEXT NOT NULL CHECK (event_type IN ('water', 'pesticide')),
            event_date TEXT NOT NULL,
            note TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (plant_id) REFERENCES plants(id)
        );
        """
    )
    cols = conn.execute("PRAGMA table_info(plants)").fetchall()
    col_names = {str(col["name"]) for col in cols}
    if "image_path" not in col_names:
        conn.execute("ALTER TABLE plants ADD COLUMN image_path TEXT DEFAULT ''")
    conn.commit()


def add_plant(
    conn: sqlite3.Connection,
    name: str,
    species: str,
    location: str,
    notes: str,
    water_interval_days: int,
    pesticide_interval_days: int,
    image_path: str = "",
) -> int:
    cur = conn.execute(
        """
        INSERT INTO plants (name, species, location, notes, image_path, water_interval_days, pesticide_interval_days)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (name, species, location, notes, image_path, water_interval_days, pesticide_interval_days),
    )
    conn.commit()
    return int(cur.lastrowid)


def list_plants(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    cur = conn.execute(
        """
        SELECT id, name, species, location, notes, image_path, water_interval_days, pesticide_interval_days, created_at
        FROM plants
        ORDER BY id ASC
        """
    )
    return list(cur.fetchall())


def get_plant(conn: sqlite3.Connection, plant_id: int) -> Optional[sqlite3.Row]:
    cur = conn.execute(
        """
        SELECT id, name, species, location, notes, image_path, water_interval_days, pesticide_interval_days, created_at
        FROM plants
        WHERE id = ?
        """,
        (plant_id,),
    )
    return cur.fetchone()


def update_plant(
    conn: sqlite3.Connection,
    plant_id: int,
    name: str,
    species: str,
    location: str,
    notes: str,
    water_interval_days: int,
    pesticide_interval_days: int,
    image_path: str,
) -> int:
    cur = conn.execute(
        """
        UPDATE plants
        SET name = ?, species = ?, location = ?, notes = ?, image_path = ?, water_interval_days = ?, pesticide_interval_days = ?
        WHERE id = ?
        """,
        (
            name,
            species,
            location,
            notes,
            image_path,
            water_interval_days,
            pesticide_interval_days,
            plant_id,
        ),
    )
    conn.commit()
    return cur.rowcount


def delete_plant(conn: sqlite3.Connection, plant_id: int) -> int:
    conn.execute("DELETE FROM events WHERE plant_id = ?", (plant_id,))
    cur = conn.execute("DELETE FROM plants WHERE id = ?", (plant_id,))
    conn.commit()
    return cur.rowcount


def add_event(
    conn: sqlite3.Connection,
    plant_id: int,
    event_type: str,
    event_date: str,
    note: str,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO events (plant_id, event_type, event_date, note)
        VALUES (?, ?, ?, ?)
        """,
        (plant_id, event_type, event_date, note),
    )
    conn.commit()
    return int(cur.lastrowid)


def list_events(conn: sqlite3.Connection, plant_id: int, event_type: str = "all") -> list[sqlite3.Row]:
    if event_type == "all":
        cur = conn.execute(
            """
            SELECT id, plant_id, event_type, event_date, note, created_at
            FROM events
            WHERE plant_id = ?
            ORDER BY event_date ASC, id ASC
            """,
            (plant_id,),
        )
    else:
        cur = conn.execute(
            """
            SELECT id, plant_id, event_type, event_date, note, created_at
            FROM events
            WHERE plant_id = ? AND event_type = ?
            ORDER BY event_date ASC, id ASC
            """,
            (plant_id, event_type),
        )
    return list(cur.fetchall())


def _last_event_date(conn: sqlite3.Connection, plant_id: int, event_type: str) -> Optional[date]:
    cur = conn.execute(
        """
        SELECT event_date
        FROM events
        WHERE plant_id = ? AND event_type = ?
        ORDER BY event_date DESC, id DESC
        LIMIT 1
        """,
        (plant_id, event_type),
    )
    row = cur.fetchone()
    if not row:
        return None
    return date.fromisoformat(row["event_date"])


def _created_at_date(plant_row: sqlite3.Row) -> date:
    ts = str(plant_row["created_at"])
    return date.fromisoformat(ts[:10])


def _safe_interval(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def build_dashboard(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    plants = list_plants(conn)
    today = date.today()
    rows: list[dict[str, Any]] = []
    for plant in plants:
        water_interval = _safe_interval(plant["water_interval_days"], 7)
        pesticide_interval = _safe_interval(plant["pesticide_interval_days"], 30)
        last_water = _last_event_date(conn, int(plant["id"]), "water") or _created_at_date(plant)
        last_pesticide = _last_event_date(conn, int(plant["id"]), "pesticide") or _created_at_date(plant)
        next_water = last_water + timedelta(days=water_interval)
        next_pesticide = last_pesticide + timedelta(days=pesticide_interval)
        rows.append(
            {
                "id": int(plant["id"]),
                "name": plant["name"],
                "species": plant["species"],
                "image_path": plant["image_path"],
                "next_water": next_water.isoformat(),
                "water_overdue": next_water < today,
                "next_pesticide": next_pesticide.isoformat(),
                "pesticide_overdue": next_pesticide < today,
            }
        )
    return rows


def _next_due_date(
    conn: sqlite3.Connection,
    plant_row: sqlite3.Row,
    event_type: str,
    interval_days: int,
) -> date:
    last = _last_event_date(conn, int(plant_row["id"]), event_type) or _created_at_date(plant_row)
    return last + timedelta(days=interval_days)


def build_alerts(
    conn: sqlite3.Connection,
    lookahead_days: int = 1,
    today: Optional[date] = None,
) -> list[dict[str, Any]]:
    current = today or date.today()
    rows: list[dict[str, Any]] = []
    for plant in list_plants(conn):
        checks = [
            ("water", _safe_interval(plant["water_interval_days"], 7), "Watering"),
            ("pesticide", _safe_interval(plant["pesticide_interval_days"], 30), "Pesticide"),
        ]
        for event_type, interval_days, label in checks:
            next_due = _next_due_date(conn, plant, event_type, interval_days)
            delta = (next_due - current).days
            if delta < 0:
                severity = "overdue"
                message = f"{label} overdue by {abs(delta)} day(s)"
            elif delta == 0:
                severity = "today"
                message = f"{label} due today"
            elif delta <= lookahead_days:
                severity = "upcoming"
                message = f"{label} due in {delta} day(s) (D-{delta})"
            else:
                continue
            rows.append(
                {
                    "plant_id": int(plant["id"]),
                    "plant_name": plant["name"],
                    "species": plant["species"],
                    "image_path": plant["image_path"],
                    "event_type": event_type,
                    "severity": severity,
                    "due_date": next_due.isoformat(),
                    "message": message,
                }
            )
    rows.sort(key=lambda item: (item["due_date"], item["plant_name"], item["event_type"]))
    return rows


def build_calendar_events(
    conn: sqlite3.Connection,
    year: int,
    month: int,
    today: Optional[date] = None,
) -> list[dict[str, Any]]:
    current = today or date.today()
    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])
    events: list[dict[str, Any]] = []

    for plant in list_plants(conn):
        checks = [
            ("water", _safe_interval(plant["water_interval_days"], 7), "Watering"),
            ("pesticide", _safe_interval(plant["pesticide_interval_days"], 30), "Pesticide"),
        ]
        for event_type, interval_days, label in checks:
            due = _next_due_date(conn, plant, event_type, interval_days)
            while due < first_day:
                due += timedelta(days=interval_days)
            while due <= last_day:
                events.append(
                    {
                        "date": due.isoformat(),
                        "plant_id": int(plant["id"]),
                        "plant_name": plant["name"],
                        "species": plant["species"],
                        "event_type": event_type,
                        "label": label,
                        "overdue": due < current,
                    }
                )
                due += timedelta(days=interval_days)

    events.sort(key=lambda item: (item["date"], item["plant_name"], item["event_type"]))
    return events

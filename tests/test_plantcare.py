from datetime import date

from plantcare.care import get_care_guide
from plantcare.db import (
    add_event,
    add_plant,
    build_alerts,
    build_calendar_events,
    build_dashboard,
    connect_db,
    ensure_schema,
    list_events,
    list_plants,
)


def test_care_guide_known_species() -> None:
    guide = get_care_guide("몬스테라")
    assert "간접광" in guide.light


def test_plant_db_and_dashboard(tmp_path) -> None:
    db_path = tmp_path / "plantcare.db"
    conn = connect_db(str(db_path))
    ensure_schema(conn)

    plant_id = add_plant(
        conn=conn,
        name="우리집 몬스테라",
        species="몬스테라",
        location="거실",
        notes="테스트",
        water_interval_days=3,
        pesticide_interval_days=10,
    )
    assert plant_id > 0
    assert len(list_plants(conn)) == 1

    add_event(conn, plant_id, "water", "2026-03-10", "물줌")
    add_event(conn, plant_id, "pesticide", "2026-03-12", "응애 약")
    history = list_events(conn, plant_id, "all")
    assert len(history) == 2

    dashboard = build_dashboard(conn)
    assert len(dashboard) == 1
    assert dashboard[0]["id"] == plant_id
    assert "next_water" in dashboard[0]
    assert "next_pesticide" in dashboard[0]

    conn.close()


def test_alerts_and_calendar(tmp_path) -> None:
    db_path = tmp_path / "plantcare2.db"
    conn = connect_db(str(db_path))
    ensure_schema(conn)

    plant_id = add_plant(
        conn=conn,
        name="My plant",
        species="Monstera",
        location="Desk",
        notes="",
        water_interval_days=3,
        pesticide_interval_days=10,
    )
    add_event(conn, plant_id, "water", "2026-03-15", "")
    add_event(conn, plant_id, "pesticide", "2026-03-01", "")

    alerts = build_alerts(conn, lookahead_days=1, today=date(2026, 3, 18))
    assert any(row["event_type"] == "water" and row["severity"] in {"today", "upcoming"} for row in alerts)
    assert any(row["event_type"] == "pesticide" and row["severity"] == "overdue" for row in alerts)

    events = build_calendar_events(conn, year=2026, month=3, today=date(2026, 3, 18))
    assert any(ev["event_type"] == "water" for ev in events)
    assert all(ev["date"].startswith("2026-03-") for ev in events)
    conn.close()

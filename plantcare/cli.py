import argparse
from datetime import date
from typing import Optional

from .care import get_care_guide
from .db import (
    add_event,
    add_plant,
    build_dashboard,
    connect_db,
    ensure_schema,
    get_plant,
    list_events,
    list_plants,
)


def _parse_date_or_today(raw: Optional[str]) -> str:
    if not raw:
        return date.today().isoformat()
    return date.fromisoformat(raw).isoformat()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="plantcare", description="식물 관리 시스템 CLI")
    parser.add_argument("--db", default="./plantcare.db", help="SQLite DB file path")
    sub = parser.add_subparsers(dest="command", required=True)

    add_cmd = sub.add_parser("add-plant", help="식물 등록")
    add_cmd.add_argument("--name", required=True)
    add_cmd.add_argument("--species", required=True)
    add_cmd.add_argument("--location", default="")
    add_cmd.add_argument("--notes", default="")
    add_cmd.add_argument("--water-interval", type=int, default=7)
    add_cmd.add_argument("--pesticide-interval", type=int, default=30)

    sub.add_parser("list-plants", help="식물 목록 조회")

    care_cmd = sub.add_parser("care", help="식물 키우는 방법 조회")
    care_cmd.add_argument("--species", help="식물 종 이름")
    care_cmd.add_argument("--plant-id", type=int, help="등록된 식물 ID")

    water_cmd = sub.add_parser("log-water", help="물주기 기록")
    water_cmd.add_argument("--plant-id", required=True, type=int)
    water_cmd.add_argument("--date", dest="event_date")
    water_cmd.add_argument("--note", default="")

    pesticide_cmd = sub.add_parser("log-pesticide", help="해충약 기록")
    pesticide_cmd.add_argument("--plant-id", required=True, type=int)
    pesticide_cmd.add_argument("--date", dest="event_date")
    pesticide_cmd.add_argument("--note", default="")

    history_cmd = sub.add_parser("history", help="식물 이력 조회")
    history_cmd.add_argument("--plant-id", required=True, type=int)
    history_cmd.add_argument("--type", choices=["all", "water", "pesticide"], default="all")

    sub.add_parser("dashboard", help="다음 물주기/해충약 일정 조회")
    return parser


def _require_plant(conn, plant_id: int):
    plant = get_plant(conn, plant_id)
    if not plant:
        raise ValueError(f"Plant id={plant_id} not found.")
    return plant


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    conn = connect_db(args.db)
    ensure_schema(conn)

    try:
        if args.command == "add-plant":
            plant_id = add_plant(
                conn=conn,
                name=args.name,
                species=args.species,
                location=args.location,
                notes=args.notes,
                water_interval_days=args.water_interval,
                pesticide_interval_days=args.pesticide_interval,
            )
            print(f"[OK] plant added id={plant_id}")

        elif args.command == "list-plants":
            rows = list_plants(conn)
            if not rows:
                print("등록된 식물이 없습니다.")
                return 0
            for row in rows:
                print(
                    f"{row['id']}. {row['name']} ({row['species']}) "
                    f"물주기 {row['water_interval_days']}일 / 해충약 {row['pesticide_interval_days']}일"
                )

        elif args.command == "care":
            species = args.species
            if args.plant_id is not None:
                plant = _require_plant(conn, args.plant_id)
                species = plant["species"]
            if not species:
                raise ValueError("Use --species or --plant-id for care command.")
            guide = get_care_guide(species)
            print(f"[{species}] 관리 가이드")
            print(f"- 빛: {guide.light}")
            print(f"- 물주기: {guide.watering}")
            print(f"- 습도: {guide.humidity}")
            print(f"- 참고: {guide.notes}")

        elif args.command == "log-water":
            _require_plant(conn, args.plant_id)
            event_date = _parse_date_or_today(args.event_date)
            event_id = add_event(conn, args.plant_id, "water", event_date, args.note)
            print(f"[OK] water event logged id={event_id} date={event_date}")

        elif args.command == "log-pesticide":
            _require_plant(conn, args.plant_id)
            event_date = _parse_date_or_today(args.event_date)
            event_id = add_event(conn, args.plant_id, "pesticide", event_date, args.note)
            print(f"[OK] pesticide event logged id={event_id} date={event_date}")

        elif args.command == "history":
            _require_plant(conn, args.plant_id)
            rows = list_events(conn, args.plant_id, event_type=args.type)
            if not rows:
                print("기록이 없습니다.")
                return 0
            for row in rows:
                print(f"{row['event_date']} | {row['event_type']} | {row['note']}")

        elif args.command == "dashboard":
            rows = build_dashboard(conn)
            if not rows:
                print("등록된 식물이 없습니다.")
                return 0
            for row in rows:
                water_mark = "지연" if row["water_overdue"] else "정상"
                pesticide_mark = "지연" if row["pesticide_overdue"] else "정상"
                print(
                    f"{row['id']}. {row['name']} ({row['species']}) | "
                    f"다음 물주기 {row['next_water']} [{water_mark}] | "
                    f"다음 해충약 {row['next_pesticide']} [{pesticide_mark}]"
                )
        return 0
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        return 1
    finally:
        conn.close()

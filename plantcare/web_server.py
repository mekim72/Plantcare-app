import argparse

from .web import create_app


def main() -> int:
    parser = argparse.ArgumentParser(prog="plantcare-web", description="PlantCare 웹 UI 서버")
    parser.add_argument("--db", default="./plantcare.db", help="SQLite DB file path")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    app = create_app({"PLANTCARE_DB": args.db})
    app.run(host=args.host, port=args.port, debug=args.debug)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


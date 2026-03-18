import os
from calendar import monthcalendar
from calendar import month_name
from datetime import date
from pathlib import Path
from typing import Optional
from uuid import uuid4

from flask import Flask, abort, flash, g, redirect, render_template, request, send_from_directory, url_for
from werkzeug.utils import secure_filename

from .care import get_care_guide
from .db import (
    add_event,
    add_plant,
    build_alerts,
    build_calendar_events,
    build_dashboard,
    connect_db,
    delete_plant,
    ensure_schema,
    get_plant,
    list_events,
    list_plants,
    update_plant,
)


def _shift_month(year: int, month: int, offset: int) -> tuple[int, int]:
    value = (year * 12 + (month - 1)) + offset
    return value // 12, (value % 12) + 1


def _parse_interval(raw_value: str, default: int) -> int:
    try:
        parsed = int(raw_value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def create_app(test_config: Optional[dict] = None) -> Flask:
    project_root = Path(__file__).resolve().parent.parent
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_mapping(
        SECRET_KEY=os.getenv("PLANTCARE_SECRET_KEY", "dev-secret"),
        PLANTCARE_DB=os.getenv("PLANTCARE_DB", "./plantcare.db"),
        PLANTCARE_UPLOAD_DIR=os.getenv("PLANTCARE_UPLOAD_DIR", "./plantcare_uploads"),
    )
    if test_config:
        app.config.update(test_config)

    db_cfg = Path(str(app.config["PLANTCARE_DB"]))
    if not db_cfg.is_absolute():
        db_cfg = (project_root / db_cfg).resolve()
    app.config["PLANTCARE_DB"] = str(db_cfg)

    upload_cfg = Path(str(app.config["PLANTCARE_UPLOAD_DIR"]))
    if not upload_cfg.is_absolute():
        upload_cfg = (project_root / upload_cfg).resolve()
    app.config["PLANTCARE_UPLOAD_DIR"] = str(upload_cfg)

    upload_dir = upload_cfg
    upload_dir.mkdir(parents=True, exist_ok=True)

    def _save_image(file_obj) -> str:
        if not file_obj or not file_obj.filename:
            return ""
        ext = Path(file_obj.filename).suffix.lower()
        if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
            raise ValueError("Only jpg/jpeg/png/webp/gif are allowed.")
        safe_base = secure_filename(Path(file_obj.filename).stem) or "plant"
        filename = f"{safe_base}-{uuid4().hex[:12]}{ext}"
        out_path = upload_dir / filename
        file_obj.save(str(out_path))
        return filename

    def _delete_image(filename: str) -> None:
        if not filename:
            return
        safe_name = secure_filename(filename)
        if not safe_name or safe_name != filename:
            return
        path = upload_dir / safe_name
        if path.exists():
            path.unlink()

    def _db():
        if "db" not in g:
            g.db = connect_db(app.config["PLANTCARE_DB"])
            ensure_schema(g.db)
        return g.db

    @app.context_processor
    def inject_sidebar_data():
        try:
            today = date.today()

            events = build_calendar_events(_db(), year=today.year, month=today.month)
            day_events: dict[int, list[dict]] = {}
            for ev in events:
                day = int(str(ev["date"]).split("-")[-1])
                day_events.setdefault(day, []).append(ev)

            return {
                "sidebar_plants": list_plants(_db()),
                "sidebar_month_title": f"{month_name[today.month]} {today.year}",
                "sidebar_year": today.year,
                "sidebar_month": today.month,
                "sidebar_weeks": monthcalendar(today.year, today.month),
                "sidebar_day_events": day_events,
                "sidebar_today_day": today.day,
            }
        except Exception:
            return {
                "sidebar_plants": [],
                "sidebar_month_title": "",
                "sidebar_year": None,
                "sidebar_month": None,
                "sidebar_weeks": [],
                "sidebar_day_events": {},
                "sidebar_today_day": None,
            }

    @app.teardown_appcontext
    def close_db(_error=None):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.get("/")
    def dashboard():
        rows = build_dashboard(_db())
        alerts = build_alerts(_db(), lookahead_days=1)
        return render_template("dashboard.html", rows=rows, alerts=alerts)

    @app.get("/calendar")
    def calendar_view():
        today = date.today()
        year = int(request.args.get("year", today.year))
        month = int(request.args.get("month", today.month))
        if month < 1 or month > 12:
            month = today.month
        events = build_calendar_events(_db(), year=year, month=month)

        grouped: dict[str, list[dict]] = {}
        for item in events:
            grouped.setdefault(item["date"], []).append(item)

        prev_year, prev_month = _shift_month(year, month, -1)
        next_year, next_month = _shift_month(year, month, 1)
        title = f"{month_name[month]} {year}"
        return render_template(
            "calendar.html",
            title=title,
            grouped=grouped,
            year=year,
            month=month,
            prev_year=prev_year,
            prev_month=prev_month,
            next_year=next_year,
            next_month=next_month,
        )

    @app.get("/plants")
    def plants():
        rows = list_plants(_db())
        return render_template("plants.html", plants=rows)

    @app.get("/plants/delete")
    def plants_delete_list():
        rows = list_plants(_db())
        return render_template("plants_delete.html", plants=rows)

    @app.get("/uploads/<path:filename>")
    def uploaded_file(filename: str):
        safe_name = secure_filename(filename)
        if not safe_name or safe_name != filename:
            abort(404)
        return send_from_directory(str(upload_dir), safe_name)

    @app.route("/plants/new", methods=["GET", "POST"])
    def new_plant():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            species = request.form.get("species", "").strip()
            if not name or not species:
                flash("Name and species are required.", "error")
                return render_template("new_plant.html")

            location = request.form.get("location", "").strip()
            notes = request.form.get("notes", "").strip()
            water_interval = _parse_interval(request.form.get("water_interval", "7"), 7)
            pesticide_interval = _parse_interval(request.form.get("pesticide_interval", "30"), 30)
            image_path = ""
            try:
                image_path = _save_image(request.files.get("image"))
            except ValueError as exc:
                flash(str(exc), "error")
                return render_template("new_plant.html")
            plant_id = add_plant(
                conn=_db(),
                name=name,
                species=species,
                location=location,
                notes=notes,
                water_interval_days=water_interval,
                pesticide_interval_days=pesticide_interval,
                image_path=image_path,
            )
            return redirect(url_for("plant_detail", plant_id=plant_id))
        return render_template("new_plant.html")

    @app.get("/plants/<int:plant_id>")
    def plant_detail(plant_id: int):
        plant = get_plant(_db(), plant_id)
        if not plant:
            flash(f"Plant id={plant_id} not found.", "error")
            return redirect(url_for("plants"))
        guide = get_care_guide(plant["species"])
        events = list_events(_db(), plant_id, event_type="all")
        return render_template(
            "plant_detail.html",
            plant=plant,
            guide=guide,
            events=events,
            today=date.today().isoformat(),
        )

    @app.get("/plants/<int:plant_id>/edit")
    def edit_plant_page(plant_id: int):
        plant = get_plant(_db(), plant_id)
        if not plant:
            flash(f"Plant id={plant_id} not found.", "error")
            return redirect(url_for("plants"))
        return render_template("edit_plant.html", plant=plant)

    @app.get("/plants/<int:plant_id>/delete")
    def delete_plant_page(plant_id: int):
        plant = get_plant(_db(), plant_id)
        if not plant:
            flash(f"Plant id={plant_id} not found.", "error")
            return redirect(url_for("plants_delete_list"))
        return render_template("delete_plant.html", plant=plant)

    @app.post("/plants/<int:plant_id>/update")
    def update_plant_info(plant_id: int):
        plant = get_plant(_db(), plant_id)
        if not plant:
            flash(f"Plant id={plant_id} not found.", "error")
            return redirect(url_for("plants"))

        name = request.form.get("name", "").strip()
        species = request.form.get("species", "").strip()
        if not name or not species:
            flash("Name and species are required.", "error")
            return redirect(url_for("edit_plant_page", plant_id=plant_id))

        location = request.form.get("location", "").strip()
        notes = request.form.get("notes", "").strip()
        water_interval = _parse_interval(request.form.get("water_interval", str(plant["water_interval_days"])), 7)
        pesticide_interval = _parse_interval(
            request.form.get("pesticide_interval", str(plant["pesticide_interval_days"])),
            30,
        )
        current_image = str(plant["image_path"] or "")
        remove_image = request.form.get("remove_image", "") == "1"
        new_upload = request.files.get("image")
        new_image = current_image

        try:
            if new_upload and new_upload.filename:
                uploaded = _save_image(new_upload)
                if current_image:
                    _delete_image(current_image)
                new_image = uploaded
            elif remove_image and current_image:
                _delete_image(current_image)
                new_image = ""
        except ValueError as exc:
            flash(str(exc), "error")
            return redirect(url_for("edit_plant_page", plant_id=plant_id))

        update_plant(
            conn=_db(),
            plant_id=plant_id,
            name=name,
            species=species,
            location=location,
            notes=notes,
            water_interval_days=water_interval,
            pesticide_interval_days=pesticide_interval,
            image_path=new_image,
        )
        flash("Plant information updated.", "success")
        return redirect(url_for("plant_detail", plant_id=plant_id))

    @app.post("/plants/<int:plant_id>/delete")
    def delete_plant_info(plant_id: int):
        plant = get_plant(_db(), plant_id)
        if not plant:
            flash(f"Plant id={plant_id} not found.", "error")
            return redirect(url_for("plants"))

        image_path = str(plant["image_path"] or "")
        deleted = delete_plant(_db(), plant_id=plant_id)
        if deleted:
            _delete_image(image_path)
            flash(f"Plant id={plant_id} deleted.", "success")
        else:
            flash("Delete failed.", "error")
        return redirect(url_for("plants"))

    def _log_event(plant_id: int, event_type: str):
        plant = get_plant(_db(), plant_id)
        if not plant:
            flash(f"Plant id={plant_id} not found.", "error")
            return redirect(url_for("plants"))

        raw_date = request.form.get("event_date", "").strip()
        event_date = raw_date or date.today().isoformat()
        note = request.form.get("note", "").strip()
        try:
            event_date = date.fromisoformat(event_date).isoformat()
        except ValueError:
            flash("Date format must be YYYY-MM-DD.", "error")
            return redirect(url_for("plant_detail", plant_id=plant_id))

        add_event(_db(), plant_id=plant_id, event_type=event_type, event_date=event_date, note=note)
        return redirect(url_for("plant_detail", plant_id=plant_id))

    @app.post("/plants/<int:plant_id>/water")
    def log_water(plant_id: int):
        return _log_event(plant_id, "water")

    @app.post("/plants/<int:plant_id>/pesticide")
    def log_pesticide(plant_id: int):
        return _log_event(plant_id, "pesticide")

    return app


app = create_app()

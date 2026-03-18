import io

from plantcare.web import create_app


def test_web_plant_flow(tmp_path) -> None:
    db_path = tmp_path / "web.db"
    app = create_app(
        {
            "TESTING": True,
            "PLANTCARE_DB": str(db_path),
            "SECRET_KEY": "test",
        }
    )
    client = app.test_client()

    res = client.get("/")
    assert res.status_code == 200

    res = client.post(
        "/plants/new",
        data={
            "name": "웹 몬스테라",
            "species": "몬스테라",
            "location": "거실",
            "notes": "테스트",
            "water_interval": "5",
            "pesticide_interval": "20",
        },
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert "웹 몬스테라" in res.get_data(as_text=True)

    res = client.post(
        "/plants/1/water",
        data={"event_date": "2026-03-18", "note": "물줌"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    text = res.get_data(as_text=True)
    assert "2026-03-18" in text

    res = client.get("/calendar?year=2026&month=3")
    assert res.status_code == 200
    assert "Calendar" in res.get_data(as_text=True)


def test_web_upload_image(tmp_path) -> None:
    db_path = tmp_path / "web_image.db"
    upload_dir = tmp_path / "uploads"
    app = create_app(
        {
            "TESTING": True,
            "PLANTCARE_DB": str(db_path),
            "PLANTCARE_UPLOAD_DIR": str(upload_dir),
            "SECRET_KEY": "test",
        }
    )
    client = app.test_client()
    image_bytes = io.BytesIO(b"\x89PNG\r\n\x1a\nfakepng")

    res = client.post(
        "/plants/new",
        data={
            "name": "Image Plant",
            "species": "Monstera",
            "location": "Desk",
            "notes": "has image",
            "water_interval": "7",
            "pesticide_interval": "30",
            "image": (image_bytes, "plant.png"),
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert res.status_code == 200
    text = res.get_data(as_text=True)
    assert "/uploads/" in text

    files = list(upload_dir.glob("*.png"))
    assert len(files) == 1

    res = client.get(f"/uploads/{files[0].name}")
    assert res.status_code == 200


def test_web_update_and_delete(tmp_path) -> None:
    db_path = tmp_path / "web_update.db"
    app = create_app(
        {
            "TESTING": True,
            "PLANTCARE_DB": str(db_path),
            "SECRET_KEY": "test",
        }
    )
    client = app.test_client()

    res = client.post(
        "/plants/new",
        data={
            "name": "Old Name",
            "species": "Monstera",
            "location": "Desk",
            "notes": "old",
            "water_interval": "7",
            "pesticide_interval": "30",
        },
        follow_redirects=True,
    )
    assert res.status_code == 200

    res = client.get("/plants/1/edit")
    assert res.status_code == 200
    assert "Edit Plant" in res.get_data(as_text=True)

    res = client.post(
        "/plants/1/update",
        data={
            "name": "New Name",
            "species": "Monstera Deliciosa",
            "location": "Living Room",
            "notes": "updated",
            "water_interval": "4",
            "pesticide_interval": "21",
        },
        follow_redirects=True,
    )
    assert res.status_code == 200
    text = res.get_data(as_text=True)
    assert "Plant information updated." in text
    assert "New Name" in text
    assert "Monstera Deliciosa" in text

    res = client.post("/plants/1/water", data={"event_date": "2026-03-18", "note": "logged"}, follow_redirects=True)
    assert res.status_code == 200

    res = client.get("/plants/delete")
    assert res.status_code == 200
    assert "Delete Plant" in res.get_data(as_text=True)

    res = client.get("/plants/1/delete")
    assert res.status_code == 200
    assert "Confirm Delete" in res.get_data(as_text=True)

    res = client.post("/plants/1/delete", follow_redirects=True)
    assert res.status_code == 200
    text = res.get_data(as_text=True)
    assert "deleted" in text
    assert "New Name" not in text


def test_sidebar_day_detail_markup_on_dashboard(tmp_path) -> None:
    db_path = tmp_path / "web_calendar_day.db"
    app = create_app(
        {
            "TESTING": True,
            "PLANTCARE_DB": str(db_path),
            "SECRET_KEY": "test",
        }
    )
    client = app.test_client()

    res = client.post(
        "/plants/new",
        data={
            "name": "Calendar Plant",
            "species": "Monstera",
            "location": "Desk",
            "notes": "",
            "water_interval": "7",
            "pesticide_interval": "30",
        },
        follow_redirects=True,
    )
    assert res.status_code == 200

    res = client.post("/plants/1/water", data={"event_date": "2026-03-18", "note": "done"}, follow_redirects=True)
    assert res.status_code == 200

    res = client.get("/")
    assert res.status_code == 200
    text = res.get_data(as_text=True)
    assert 'id="sidebar-day-detail"' in text
    assert 'id="sidebar-events-json"' in text
    assert "Calendar Plant" in text

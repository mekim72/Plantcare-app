# PlantCare Deployment Guide

This project now includes deployment-ready files for three common paths:

- `Procfile`: Heroku-like platforms
- `render.yaml`: Render blueprint deployment
- `Dockerfile`: Docker-based deployment (Railway, Fly.io, VPS, etc.)

## 1) Render (Recommended)

1. Push this repository to GitHub.
2. In Render, choose **New +** -> **Blueprint**.
3. Select this repository.
4. Render will detect `render.yaml` and create:
- web service: `plantcare-web`
- persistent disk mounted at `/var/data`
5. Deploy.

Environment variables are already defined in `render.yaml`:

- `PLANTCARE_SECRET_KEY` (auto-generated)
- `PLANTCARE_DB=/var/data/plantcare.db`
- `PLANTCARE_UPLOAD_DIR=/var/data/uploads`

## 2) Procfile-based deploy

The app can be started with:

```bash
gunicorn plantcare.web:app --bind 0.0.0.0:$PORT
```

`Procfile` already includes this command.

Set these environment variables on your platform:

- `PLANTCARE_SECRET_KEY`
- `PLANTCARE_DB`
- `PLANTCARE_UPLOAD_DIR`

## 3) Docker deploy

Build and run locally:

```bash
docker build -t plantcare-web .
docker run --rm -p 5000:5000 -e PORT=5000 -v ${PWD}/data:/data plantcare-web
```

Then open `http://127.0.0.1:5000`.

## Notes

- Use persistent storage for both database and uploaded images.
- If no env vars are set, local defaults still work in development.

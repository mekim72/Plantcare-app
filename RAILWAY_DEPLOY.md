# Railway Deployment Guide

## 1) Create project

1. Open Railway dashboard.
2. Create `New Project` -> `Deploy from GitHub repo`.
3. Select this repository.

`railway.json` is already included, so Railway will use:

- Start command: `gunicorn plantcare.web:app --bind 0.0.0.0:$PORT`
- Health check: `/healthz`

## 2) Environment variables

Set these variables in Railway project settings:

- `PLANTCARE_SECRET_KEY`: random long string
- `PLANTCARE_DB`: `/data/plantcare.db`
- `PLANTCARE_UPLOAD_DIR`: `/data/uploads`

If you do not use a persistent volume, use `/tmp/...` instead:

- `PLANTCARE_DB=/tmp/plantcare.db`
- `PLANTCARE_UPLOAD_DIR=/tmp/uploads`

## 3) Persistent storage (recommended)

For stable data/image retention:

1. Add a Railway Volume.
2. Mount path: `/data`
3. Keep env vars as:
- `PLANTCARE_DB=/data/plantcare.db`
- `PLANTCARE_UPLOAD_DIR=/data/uploads`

Without volume, data can be lost on restart/redeploy.

## 4) Deploy and open URL

1. Trigger deploy (auto on push or manual).
2. Open generated public domain in Railway.
3. Verify:
- `GET /healthz` returns 200
- main page loads at `/`

# GitHub Actions -> PythonAnywhere Auto Deploy

This project includes a GitHub Actions workflow at:

- `.github/workflows/deploy-pythonanywhere.yml`

When code is pushed to `main`, it deploys to PythonAnywhere via SSH.

## 1) Prepare PythonAnywhere server once

Run these commands in PythonAnywhere Bash console:

```bash
cd ~
git clone https://github.com/mekim72/plantcare-app.git
cd plantcare-app
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdir -p plantcare_uploads
```

Set your WSGI file to use these env vars:

- `PLANTCARE_SECRET_KEY`
- `PLANTCARE_DB=/home/<USERNAME>/plantcare-app/plantcare.db`
- `PLANTCARE_UPLOAD_DIR=/home/<USERNAME>/plantcare-app/plantcare_uploads`

## 2) Add GitHub repository secrets

In GitHub -> `Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret`, add:

- `PA_SSH_HOST`: `ssh.pythonanywhere.com`
- `PA_SSH_PORT`: `22`
- `PA_SSH_USER`: your PythonAnywhere username
- `PA_SSH_KEY`: private SSH key text (OpenSSH format)
- `PA_PROJECT_DIR`: `/home/<USERNAME>/plantcare-app`
- `PA_WSGI_FILE`: `/var/www/<USERNAME>_pythonanywhere_com_wsgi.py`

## 3) Trigger deployment

- Push to `main`, or
- Run manually from GitHub Actions (`workflow_dispatch`).

## Notes

- If your PythonAnywhere plan does not allow SSH, this workflow cannot connect.
- In that case, deploy manually in PythonAnywhere Bash console (`git pull`, `pip install -r requirements.txt`, Reload web app).

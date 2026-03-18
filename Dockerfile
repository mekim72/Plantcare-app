FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

ENV PLANTCARE_DB=/data/plantcare.db
ENV PLANTCARE_UPLOAD_DIR=/data/uploads
ENV PORT=5000

RUN mkdir -p /data/uploads

EXPOSE 5000

CMD ["sh", "-c", "gunicorn plantcare.web:app --bind 0.0.0.0:${PORT}"]

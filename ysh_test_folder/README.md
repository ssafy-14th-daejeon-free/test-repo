# Django velog Clone MVP

A Django-only blog MVP inspired by velog. Django Templates handle the front end and Django views/models handle the back end.

## Run

### Docker Compose with PostgreSQL

```powershell
docker compose up -d --build
```

Then open:

```text
http://127.0.0.1:8000/
```

The compose setup runs two services:

- `db`: PostgreSQL with a named Docker volume
- `app`: Django app container built from `Dockerfile`

The app waits for PostgreSQL, runs migrations, collects static files, and starts Django on port `8000`.

### Local Python with SQLite

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python manage.py migrate
.\.venv\Scripts\python manage.py runserver
```

## Features

- Sign up, login, logout, and profile pages
- Markdown post create, read, update, and delete
- Trending/latest/feed-style post list tabs
- Tag pages and search
- Like toggle for logged-in users
- Comments and series
- Optional cover image URLs for velog-style cards
- Folder-local test login with `localtester`
- Drafts stored in local SQLite, not browser storage
- Follow, notifications, and local stats dashboard
- Advanced Markdown editor with toolbar and live preview

## Local-only storage

This project is intended for localhost testing. With local Python, application state is stored in this folder through `db.sqlite3`. With Docker Compose, application state is stored in the local Docker PostgreSQL volume declared in `docker-compose.yaml`. The editor preview uses JavaScript for interaction, but draft persistence is handled by Django and the configured database rather than browser `localStorage`.

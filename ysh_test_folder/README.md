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

Docker Compose binds the app to `127.0.0.1:8000`, runs with `DJANGO_DEBUG=0`, and enables the local test login only for localhost testing.

### Local Python with SQLite

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python manage.py migrate
.\.venv\Scripts\python manage.py runserver --insecure
```

For direct local Python testing with the `localtester` shortcut:

```powershell
$env:ENABLE_LOCAL_LOGIN='1'
```

## Features

- Sign up, login, logout, and profile pages
- Markdown post create, read, update, and delete
- Trending/latest/feed-style post list tabs
- Tag pages and search
- Like toggle for logged-in users
- Comments and series
- Optional cover image URLs for velog-style cards
- Folder-local test login with `localtester` when explicitly enabled
- Drafts stored in local SQLite, not browser storage
- Follow, notifications, and local stats dashboard
- Advanced Markdown editor with toolbar and live preview

## Local-only storage

This project is intended for localhost testing. With local Python, application state is stored in this folder through `db.sqlite3`. With Docker Compose, application state is stored in the local Docker PostgreSQL volume declared in `docker-compose.yaml`. The editor preview uses JavaScript for interaction, but draft persistence is handled by Django and the configured database rather than browser `localStorage`.

## Security notes

- `DEBUG` defaults to off and Docker Compose keeps it off.
- `SECRET_KEY` is loaded from `DJANGO_SECRET_KEY` or generated into `.local/django-secret-key`, which is ignored by git and Docker builds.
- `/accounts/local-login/` requires `ENABLE_LOCAL_LOGIN=1` and a localhost host header.
- Login, signup, local-login, post create, and comment create endpoints have simple cache-backed rate limits for localhost abuse testing.
- Cover image URLs are restricted by `ALLOWED_COVER_IMAGE_HOSTS`.

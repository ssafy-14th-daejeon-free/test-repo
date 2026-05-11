# Django velog Clone MVP

A Django-only blog MVP inspired by velog. Django Templates handle the front end and Django views/models handle the back end.

## Run

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

This project is intended for localhost testing. Application state is stored in files inside this folder, primarily `db.sqlite3`. The editor preview uses JavaScript for interaction, but draft persistence is handled by Django and SQLite rather than browser `localStorage`.

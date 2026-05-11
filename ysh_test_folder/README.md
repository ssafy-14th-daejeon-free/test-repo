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

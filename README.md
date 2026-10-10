# School Scheduler

A Django application for building, validating, and presenting school timetables.

School Scheduler focuses on the operational workflow a school administrator needs: configure academic years and periods, manage teachers and teaching resources, create lessons, detect scheduling conflicts, and view the resulting timetable by teacher, student group, room, or whole school.

![Teacher timetable](docs/screenshots/teacher-timetable.png)

## Features

- Weekly timetable views for teachers, student groups, rooms, and the whole school
- Compact lesson cards with context-aware details and consistent subject colors
- Academic year and period configuration, including lesson periods and breaks
- CRUD workflows for teachers, rooms, subjects, student groups, lessons, academic years, and periods
- Conflict detection for teacher, room, and student group double-booking
- Planned substitute generation and teacher availability lookup
- Staff-only editing with public timetable viewing
- Demo data command for quickly exploring a realistic schedule

## Architecture

The project follows the simplified Clean Architecture approach described in `PROJECT_BLUEPRINT.md`.

- `app/domain`: pure Python scheduling models, policies, and domain exceptions
- `app/application`: use-case services and repository ports
- `app/infrastructure`: Django ORM models and repository implementations
- `app/presentation`: Django views, forms, renderers, templates, and navigation
- `app/management`: demo data and operational management commands
- `tests`: domain, application, infrastructure, presentation, and integration tests

Scheduling rules live in the domain and application layers. The web interface calls the application services for lesson creation and updates, so validation remains consistent across the UI and tests.

## Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Database

**PostgreSQL is the project's standard database backend, for local development, testing, and production alike — there is no SQLite fallback.** Connection settings always come from environment variables (never hardcoded), so the same `config/settings.py` works unchanged everywhere; only the environment differs.

### Local PostgreSQL setup (macOS)

Install and start PostgreSQL via Homebrew if you don't already have it running:

```bash
brew install postgresql@16
brew services start postgresql@16
```

Create a dedicated role and database for this project (`createuser`/`createdb` also work; this uses `psql` directly so the role gets `CREATEDB`, which the test suite needs to create and tear down its own isolated test database):

```bash
export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"
psql postgres -c "CREATE ROLE school_scheduler WITH LOGIN PASSWORD 'choose-a-local-password' CREATEDB;"
psql postgres -c "CREATE DATABASE school_scheduler_dev OWNER school_scheduler;"
```

### Required environment variables

Copy `.env.example` to `.env` and fill in the password you chose above:

```bash
cp .env.example .env
```

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `DB_NAME` | yes | — | Database name (e.g. `school_scheduler_dev`) |
| `DB_USER` | yes | — | Role name (e.g. `school_scheduler`) |
| `DB_PASSWORD` | yes | — | Role password |
| `DB_HOST` | no | `localhost` | Database host |
| `DB_PORT` | no | `5432` | Database port |

`.env` is gitignored and loaded automatically (via `python-dotenv`) when Django starts — nothing elsewhere in the codebase reads these variables directly; they're only ever used to build `DATABASES` in `config/settings.py`. If a required variable is missing, Django raises a clear `ImproperlyConfigured` error naming exactly which one, rather than silently falling back to any default database.

A real deployment sets these same variables directly in its own environment (never via a committed `.env`) and should point at its own separate database/instance — development and production must never share one.

### Migrations, tests, and demo data

```bash
python manage.py migrate
python manage.py load_demo_data   # optional — populates two demo schools
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

```bash
python -m pytest
```

Each test run uses its own isolated `test_<DB_NAME>` database, automatically created and destroyed by `pytest-django`/Django — your real `DB_NAME` database (and any demo data in it) is never touched by the test suite. This is why the role needs `CREATEDB`.

### Backing up and restoring

Back up with Postgres's own dump tool (adjust `DB_NAME` to match your `.env`):

```bash
pg_dump -h localhost -U school_scheduler school_scheduler_dev > backups/school_scheduler_dev.sql
```

Restore from such a dump into a fresh database:

```bash
createdb -h localhost -U school_scheduler school_scheduler_dev_restored
psql -h localhost -U school_scheduler school_scheduler_dev_restored < backups/school_scheduler_dev.sql
```

`backups/` is gitignored — dumps may contain password hashes and must never be committed.

If you need to fall back to the pre-PostgreSQL SQLite workflow temporarily (e.g. to compare behavior), the previous `DATABASES` block pointing at `db.sqlite3` is in git history on the commit before the PostgreSQL migration; `db.sqlite3` itself is untouched and still present if it exists in your checkout.

## Project Structure

```text
.
├── app/
│   ├── application/        # Use-case services and ports
│   ├── domain/             # Scheduling rules and domain objects
│   ├── infrastructure/     # Django ORM persistence
│   ├── management/         # Demo data and management commands
│   ├── presentation/       # Web UI, forms, templates, and renderers
│   └── templatetags/       # Template helpers
├── config/                 # Django project settings and URL routing
├── docs/screenshots/       # README screenshots
├── tests/                  # Unit and integration tests
├── manage.py
├── requirements.txt
└── PROJECT_BLUEPRINT.md
```

## Development Notes

- Public users can browse timetable views.
- Staff users can add and edit lessons.
- Legacy management pages remain available under `/legacy/`; Django Admin is the supported management interface for reference data.
- The scheduling algorithm, domain model, validation rules, and database schema are intentionally kept separate from presentation polish.

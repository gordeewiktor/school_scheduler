# School Scheduler

MVP Django application for creating and managing a school timetable.

## Features

- Django authentication and admin
- CRUD pages for academic years, reusable periods, teachers, rooms, subjects, student groups, and lessons
- Dynamic weekly timetable whose columns come from period definitions
- Lesson and break periods
- Multi-period lessons
- Filters by teacher, room, and student group
- Conflict detection for teacher, room, and student group double-booking

## Architecture

The project follows the simplified Clean Architecture approach from `PROJECT_BLUEPRINT.md`.

- `app/domain`: pure Python period/lesson behavior, policies, and domain exceptions
- `app/application`: services and repository ports
- `app/infrastructure`: Django ORM models and repository implementations
- `app/presentation`: Django forms, views, URLs, and templates

Business scheduling rules live in the domain/application layers. Lesson forms use `ScheduleService` as the single create/update workflow; reference and configuration models remain conventional Django models.

## Install

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run Locally

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

## Tests

```bash
pytest
```

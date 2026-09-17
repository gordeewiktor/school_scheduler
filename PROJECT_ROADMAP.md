# School Scheduler — Project Roadmap

This document tracks the implementation of the School Scheduler.

The roadmap describes what we are building and what remains.
The codebase is the source of truth for what has actually been implemented.

---

# Current Goal

Transform the current single-school scheduling application into a
multi-school application that can eventually be used by independent
schools and their principals.

The application should eventually allow a principal to:

1. Register/login.
2. Create or access their school.
3. Create an academic year.
4. Configure the school's timetable structure.
5. Add teachers, rooms, subjects, and student groups.
6. Create and manage lessons.
7. Generate and manage substitute-teacher assignments.
8. Use the scheduling system without seeing or modifying another
   school's data.

---

# Development Principles

- Make one meaningful change at a time.
- Understand the architecture before changing it.
- Prefer small, testable changes over large rewrites.
- Use Claude Code / ChatGPT as development collaborators, not as
  black-box code generators.
- Review important AI-generated changes before accepting them.
- Keep the domain layer framework-independent.
- Preserve the existing architecture unless there is a clear reason
  to change it.
- Add tests for important behavior and especially for school data
  isolation.
- Do not introduce unnecessary technologies.
- Do not build features before they are needed.
- Keep the application small enough to remain understandable.
- Deploy only after the application is sufficiently usable.

---

# Phase 0 — Understand the Existing Application

## Architecture

- [x] Inspect the complete project structure.
- [x] Identify the domain layer.
- [x] Identify the application/service layer.
- [x] Identify the infrastructure layer.
- [x] Identify the presentation layer.
- [x] Identify authentication and authorization.
- [x] Identify repositories and ports.
- [x] Identify current scheduling logic.
- [x] Identify current substitute-teacher logic.
- [x] Review existing tests.
- [x] Review `PROJECT_BLUEPRINT.md`.
- [x] Review `README.md`.
- [x] Review `structure.txt`.

## Current architecture understanding

The current architecture is approximately:

User / browser
        ↓
Presentation
        ↓
Application services
        ↓
Repository / infrastructure
        ↓
Django ORM
        ↓
Database

The domain layer contains framework-independent dataclasses and
business rules.

---

# Phase 1 — Multi-School Foundation

## Design decisions

- [x] Introduce `School` as the tenancy root.
- [x] Decide that `AcademicYear` belongs to `School`.
- [x] Decide that `Teacher` belongs to `School`.
- [x] Decide that `Room` belongs to `School`.
- [x] Decide that `Subject` belongs to `School`.
- [x] Decide that `StudentGroup` belongs to `School`.
- [x] Decide that these entities are reusable across academic years.
- [x] Decide that multiple users/staff should eventually be able to
      belong to the same school.
- [x] Keep Django's `is_staff` concept separate from school ownership.
- [x] Keep Django Admin restricted to appropriate administrative users
      during the transition.
- [ ] Decide final public timetable URL structure.

## School model

- [x] Create `School` model.
- [x] Decide required fields for School (`name`, `created_at` only; `name`
      is intentionally not unique, since real schools can share a name).
- [x] Add School migration.
- [x] Add School to admin if appropriate.
- [x] Add School tests.

## Principal / school membership

- [x] Create `Principal` / school-membership model (named `SchoolMembership`,
      with a `role` field defaulting to `PRINCIPAL`).
- [x] Connect Django `User` to School (via `SchoolMembership`, using the
      built-in `django.contrib.auth.User` — no custom user model).
- [x] Decide whether the model is a membership relationship that allows
      multiple users per school (yes — `SchoolMembership` is a join model,
      unique per `(user, school)`).
- [x] Add migrations.
- [x] Add model tests.
- [x] Create a safe way to associate the existing user with the
      existing school (`create_school` management command; not executed
      against the dev database yet — run manually when ready).

---

# Phase 2 — Academic Year Ownership

## Database

- [ ] Add `school` ForeignKey to `AcademicYear`.
- [ ] Create migration.
- [ ] Create/backfill the initial/default school.
- [ ] Assign existing AcademicYear records to the appropriate school.
- [ ] Make `AcademicYear.school` required.
- [ ] Replace global AcademicYear name uniqueness with per-school
      uniqueness.

## Application

- [ ] Update AcademicYear forms.
- [ ] Update AcademicYear views.
- [ ] Update AcademicYear services/use cases if necessary.
- [ ] Update repositories if necessary.
- [ ] Ensure a principal can only access AcademicYears belonging to
      their school.

## Tests

- [ ] Test AcademicYear belongs to School.
- [ ] Test per-school AcademicYear name uniqueness.
- [ ] Test School A cannot access School B's AcademicYear.
- [ ] Update existing fixtures.

---

# Phase 3 — School-Owned Resources

The following resources should belong directly to School and be
reusable across multiple academic years:

- Teacher
- Room
- Subject
- StudentGroup

## Teacher

- [ ] Add `school` ForeignKey.
- [ ] Migrate existing teachers.
- [ ] Make school relationship required.
- [ ] Replace global name uniqueness with per-school uniqueness.
- [ ] Update forms.
- [ ] Update views.
- [ ] Update repositories.
- [ ] Add isolation tests.

## Room

- [ ] Add `school` ForeignKey.
- [ ] Migrate existing rooms.
- [ ] Make school relationship required.
- [ ] Replace global name uniqueness with per-school uniqueness.
- [ ] Update forms.
- [ ] Update views.
- [ ] Add isolation tests.

## Subject

- [ ] Add `school` ForeignKey.
- [ ] Migrate existing subjects.
- [ ] Make school relationship required.
- [ ] Replace global name uniqueness with per-school uniqueness.
- [ ] Update forms.
- [ ] Update views.
- [ ] Add isolation tests.

## StudentGroup

- [ ] Add `school` ForeignKey.
- [ ] Migrate existing student groups.
- [ ] Make school relationship required.
- [ ] Replace global name uniqueness with per-school uniqueness.
- [ ] Update forms.
- [ ] Update views.
- [ ] Add isolation tests.

---

# Phase 4 — School Data Isolation

This is a critical security phase.

Every authenticated principal must operate inside their own school
context.

## School resolution

- [ ] Resolve the current school from the authenticated user's
      Principal/membership.
- [ ] Never trust a client-supplied school ID for authenticated
      operations.
- [ ] Establish a consistent way for views/services to obtain the
      current school.

## Query isolation

Audit and eliminate unscoped queries such as:

    Model.objects.all()

and:

    Model.objects.get(pk=some_id)

when they can expose another school's data.

- [ ] AcademicYear queries scoped by School.
- [ ] Teacher queries scoped by School.
- [ ] Room queries scoped by School.
- [ ] Subject queries scoped by School.
- [ ] StudentGroup queries scoped by School.
- [ ] Period queries scoped through AcademicYear.
- [ ] Lesson queries scoped through AcademicYear/School.
- [ ] Substitute-teacher queries scoped by School.
- [ ] Schedule queries scoped by School.

## IDOR protection

Generic Django views must not allow a principal to manipulate an
object belonging to another school by guessing its primary key.

- [ ] Audit UpdateViews.
- [ ] Audit DeleteViews.
- [ ] Audit DetailViews.
- [ ] Audit CreateViews.
- [ ] Audit custom `get_object()` calls.
- [ ] Add tests for cross-school access.

## Forms

ModelChoiceFields must not expose objects belonging to another school.

- [ ] AcademicYear choices scoped.
- [ ] Teacher choices scoped.
- [ ] Room choices scoped.
- [ ] Subject choices scoped.
- [ ] StudentGroup choices scoped.
- [ ] Period choices scoped.

---

# Phase 5 — Periods and Timetable Configuration

An AcademicYear owns its periods.

A principal should eventually be able to configure the school's
timetable structure.

## Periods

- [ ] Confirm current Period model is appropriate.
- [ ] Keep Period associated with AcademicYear.
- [ ] Ensure period order is unique within AcademicYear.
- [ ] Ensure period names are unique within AcademicYear.
- [ ] Preserve start/end-time validation.
- [ ] Support LESSON periods.
- [ ] Support BREAK periods.

## Timetable configuration

Eventually support configuration such as:

- [ ] Number of periods per day.
- [ ] Period names.
- [ ] Period order.
- [ ] Start times.
- [ ] End times.
- [ ] Breaks.
- [ ] Default lesson duration.

Avoid creating redundant configuration fields when the existing Period
model already represents the required information.

---

# Phase 6 — Lessons and Scheduling

## Lessons

- [ ] Ensure lessons are accessible only within the current school.
- [ ] Validate that the lesson's teacher belongs to the same school.
- [ ] Validate that the lesson's room belongs to the same school.
- [ ] Validate that the lesson's subject belongs to the same school.
- [ ] Validate that the lesson's student group belongs to the same
      school.
- [ ] Validate that the lesson's Period belongs to the same school.
- [ ] Prevent cross-school references.
- [ ] Add appropriate tests.

## Scheduling

- [ ] Audit ScheduleService.
- [ ] Audit ConflictService.
- [ ] Audit LessonRepository.
- [ ] Ensure all scheduling operations operate within one school.
- [ ] Confirm conflict detection cannot mix school data.
- [ ] Add multi-school service tests.

---

# Phase 7 — Substitute Teacher System

Current intended algorithm:

1. Find teachers who are not teaching during the required period.
2. Exclude teachers already assigned as substitutes during that period.
3. If candidates exist, choose the candidate with the fewest existing
   substitution assignments.
4. If no candidates exist, allow teachers who are already assigned as
   substitutes during that period.
5. Again choose the teacher with the fewest existing substitution
   assignments.

## Multi-school requirements

- [ ] Ensure teacher pool is limited to the current school.
- [ ] Ensure substitute assignments cannot cross schools.
- [ ] Audit `list_teachers()`.
- [ ] Audit `SubstitutionService`.
- [ ] Audit substitution-related repository methods.
- [ ] Add two-school isolation tests.

---

# Phase 8 — Authentication and Registration

This phase turns the application into something an external principal
could actually use.

## Login

- [ ] Confirm existing login flow.
- [ ] Connect authenticated User to Principal/School.
- [ ] Define behavior for users without a school.

## Registration

- [ ] Create registration flow.
- [ ] Allow a new user to create a School.
- [ ] Create the Principal/membership relationship.
- [ ] Perform account + school creation in one transaction.
- [ ] Prevent accidental creation of orphaned school/user records.

## Authorization

- [ ] Replace inappropriate reliance on `is_staff` for school ownership.
- [ ] Ensure principals can only manage their own school.
- [ ] Decide whether different school roles are needed.
- [ ] Add authorization tests.

---

# Phase 9 — Demo Data

- [ ] Update `load_demo_data`.
- [ ] Remove assumptions about one global AcademicYear.
- [ ] Create a demo School.
- [ ] Create a demo Principal/user if appropriate.
- [ ] Create school-specific teachers.
- [ ] Create school-specific rooms.
- [ ] Create school-specific subjects.
- [ ] Create school-specific student groups.
- [ ] Create AcademicYear for the demo school.
- [ ] Create periods and lessons.
- [ ] Verify substitute-teacher generation.

---

# Phase 10 — Testing

## Unit/domain tests

- [ ] Period validation.
- [ ] Domain scheduling rules.
- [ ] Conflict rules.
- [ ] Substitute-teacher rules.

## Application tests

- [ ] ScheduleService.
- [ ] ConflictService.
- [ ] SubstitutionService.
- [ ] Multi-school isolation.

## Infrastructure tests

- [ ] Repository filtering.
- [ ] Teacher queries.
- [ ] Lesson queries.
- [ ] AcademicYear queries.
- [ ] School-specific data access.

## Integration/web tests

- [ ] Login.
- [ ] Principal access.
- [ ] AcademicYear access.
- [ ] Teacher access.
- [ ] Room access.
- [ ] Subject access.
- [ ] StudentGroup access.
- [ ] Lesson access.
- [ ] Schedule access.
- [ ] Substitute access.
- [ ] Cross-school access attempts return 403/404 and never expose data.

## Regression

- [ ] Run complete test suite.
- [ ] Fix broken fixtures.
- [ ] Verify existing functionality still works.
- [ ] Test with at least two schools containing overlapping names/data.

---

# Phase 11 — Production Preparation

Before deployment:

- [ ] Review production Django settings.
- [ ] Move secrets to environment variables.
- [ ] Configure `DEBUG=False`.
- [ ] Configure allowed hosts.
- [ ] Configure CSRF/trusted origins appropriately.
- [ ] Configure production database.
- [ ] Configure static files.
- [ ] Configure media files if required.
- [ ] Configure logging.
- [ ] Configure error handling.
- [ ] Review authentication/security settings.
- [ ] Review school data isolation.
- [ ] Review database backups.

---

# Phase 12 — Deployment

Goal: make the application accessible over the Internet.

Possible approach:

    VPS
    ├── Django application
    ├── PostgreSQL
    ├── Gunicorn
    ├── Nginx
    ├── HTTPS
    └── Multiple small applications if desired

Tasks:

- [ ] Rent/configure VPS.
- [ ] Configure Linux server.
- [ ] Configure firewall.
- [ ] Install required packages.
- [ ] Configure PostgreSQL.
- [ ] Configure application environment.
- [ ] Configure Gunicorn.
- [ ] Configure Nginx.
- [ ] Configure domain.
- [ ] Configure HTTPS.
- [ ] Deploy application.
- [ ] Run migrations.
- [ ] Create production admin/superuser if required.
- [ ] Verify application from another device/network.
- [ ] Verify authentication.
- [ ] Verify school isolation.
- [ ] Verify backups.

---

# Phase 13 — Portfolio

- [ ] Clean Git history where appropriate.
- [ ] Write/update README.
- [ ] Explain the problem the application solves.
- [ ] Explain the architecture.
- [ ] Explain substitute-teacher algorithm.
- [ ] Add screenshots.
- [ ] Add public demo URL.
- [ ] Document technical decisions.
- [ ] Document deployment.
- [ ] Document testing.
- [ ] Make repository understandable to another developer.

---

# Current Session

## Goal

Implement the next small architectural step toward multi-school support.

## Current status

Phase 1's School/SchoolMembership foundation has been implemented
(models, migration, admin, `create_school` command, tests) but not yet
committed. The existing "principal" user has not yet been attached to a
school — `create_school` has been written but intentionally not run.

## Immediate next step

1. Review the diff.
2. Decide whether/when to run `create_school` against the dev database.
3. Commit this slice.
4. Move to Phase 2 (connect `AcademicYear` to `School`).

---

# Current Decisions

- School is the intended tenancy root.
- AcademicYear belongs to School.
- Teacher belongs to School.
- Room belongs to School.
- Subject belongs to School.
- StudentGroup belongs to School.
- These resources are intended to be reusable across academic years.
- Principal/school membership should allow for multiple users per school
  eventually.
- Django `is_staff` should remain conceptually separate from school
  ownership.
- Domain models should remain framework-independent.
- Cross-school data isolation is a critical requirement.
- Deployment is intended to make the application accessible to real
  users.
- A single VPS may eventually host multiple small applications.

---

# Open Decisions

These decisions should be made when they become relevant rather than
prematurely.

- [x] Exact fields for School — resolved: `name` (not unique), `created_at`.
- [x] Exact Principal/membership model and roles — resolved: `SchoolMembership`
      with a `role` field (currently only `PRINCIPAL`).
- [ ] Public timetable URL structure.
- [ ] Whether `school_id` should ever be denormalized onto Period/Lesson
      for defense-in-depth.
- [ ] Final Django Admin policy.
- [ ] Final registration/user onboarding flow.
- [ ] Whether public timetable browsing should be supported and how
      schools are selected.
- [ ] Production hosting provider.
- [ ] Production database provider/server configuration.

---

# Session Log

## 2026-09-17

### Completed

- Reviewed current project architecture.
- Reviewed domain models.
- Reviewed Django persistence models.
- Identified current single-school assumptions.
- Identified multi-school architecture requirements.
- Created initial multi-school roadmap.
- Implemented the Phase 1 School + SchoolMembership foundation:
  `School` and `SchoolMembership` models, an additive migration
  (`0006_school_schoolmembership`), admin registration for both, and a
  `create_school` management command (written but not executed against
  the dev database).
- Added model tests (`tests/infrastructure/test_school_models.py`) and
  command tests (`tests/integration/test_create_school_command.py`).
- Ran `makemigrations --check`, `manage.py check`, and the full pytest
  suite: 120 passed, 1 pre-existing failure unrelated to this change
  (`test_administrator_navigation`, confirmed failing on the base branch
  before these changes too).
- No existing models, views, forms, repositories, services, or
  authentication logic were modified.

### Current task

Phase 1's School/SchoolMembership foundation is implemented but not yet
committed, and the existing user has not yet been attached to a school.

### Next

Review the diff, decide whether/when to run `create_school` against the
dev database, then move to Phase 2 (connect `AcademicYear` to `School`).
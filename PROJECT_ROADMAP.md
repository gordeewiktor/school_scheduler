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

- [x] Add `school` ForeignKey to `AcademicYear`.
- [x] Create migration (split into three: nullable add, data backfill,
      then required + constraint — `0007`, `0008`, `0009`).
- [x] Create/backfill the initial/default school (data migration
      `get_or_create`s a "Default School" for any orphaned rows).
- [x] Assign existing AcademicYear records to the appropriate school
      (verified against the real dev database: the existing "Demo 2026"
      AcademicYear is now owned by "Default School").
- [x] Make `AcademicYear.school` required.
- [x] Replace global AcademicYear name uniqueness with per-school
      uniqueness (`UniqueConstraint(school, name)`).

## Application

- [x] Update AcademicYear forms (`AcademicYearForm` now includes
      `school`, unscoped — any school can be picked; scoping is Phase 4).
- [x] Update AcademicYear views (`AcademicYearListView` shows a School
      column).
- [x] Update AcademicYear services/use cases if necessary — not needed;
      `ScheduleService`/`ConflictService`/`SubstitutionService` only ever
      operate on an opaque `academic_year_id`.
- [x] Update repositories if necessary — not needed, same reason.
- [ ] Ensure a principal can only access AcademicYears belonging to
      their school — intentionally deferred to Phase 4
      (school resolution/scoping is out of scope for this slice).

## Tests

- [x] Test AcademicYear belongs to School (`IntegrityError` without one).
- [x] Test per-school AcademicYear name uniqueness.
- [x] Test different schools can share an AcademicYear name.
- [x] Test the data-migration backfill itself, using Django's
      `MigrationExecutor` against historical model states (not just the
      end state) — covers a single orphaned row and multiple orphaned
      rows sharing one "Default School".
- [x] Update existing fixtures (5 test files, ~15 call sites updated to
      pass an explicit `school=`).
- [ ] Test School A cannot access School B's AcademicYear — deferred to
      Phase 4 along with school-scoped access itself.

---

# Phase 3 — School-Owned Resources

The following resources should belong directly to School and be
reusable across multiple academic years:

- Teacher
- Room
- Subject
- StudentGroup

## Teacher

- [x] Add `school` ForeignKey.
- [x] Migrate existing teachers.
- [x] Make school relationship required.
- [x] Replace global name uniqueness with per-school uniqueness.
- [x] Update forms.
- [x] Update views.
- [x] Update repositories.
- [x] Add isolation tests.

## Room

- [x] Add `school` ForeignKey.
- [x] Migrate existing rooms.
- [x] Make school relationship required.
- [x] Replace global name uniqueness with per-school uniqueness.
- [x] Update forms.
- [x] Update views.
- [x] Add isolation tests.

## Subject

- [x] Add `school` ForeignKey.
- [x] Migrate existing subjects.
- [x] Make school relationship required.
- [x] Replace global name uniqueness with per-school uniqueness.
- [x] Update forms.
- [x] Update views.
- [x] Add isolation tests.

## StudentGroup

- [x] Add `school` ForeignKey.
- [x] Migrate existing student groups.
- [x] Make school relationship required.
- [x] Replace global name uniqueness with per-school uniqueness.
- [x] Update forms.
- [x] Update views.
- [x] Add isolation tests.

## Notes

- `Subject.code` was left untouched — it had no uniqueness constraint
  before Phase 3 and none was added.
- `Meta.ordering` for all four models is `["school", "name"]`.
- Migrations: `0010_school_owned_resources_nullable` (nullable
  `AddField` for all four models) → `0011_backfill_school_owned_resources`
  (`RunPython`, reuses Phase 2's "Default School" by name via
  `get_or_create` rather than creating a second one) →
  `0012_school_owned_resources_required` (required FK + per-school
  `UniqueConstraint` + ordering, for all four models). Applied to the
  real `db.sqlite3`; verified 80 Teachers / 42 Rooms / 10 Subjects / 42
  StudentGroups / 2100 Lessons preserved and all owned by the same
  "Default School" that already owned "Demo 2026".
- Two safeguards from later phases were pulled forward narrowly because
  Phase 3 made them necessary — see the Phase 6 and Phase 7 notes below.

---

# Phase 4 — School Data Isolation

This is a critical security phase. It is split into four small,
independently-reviewable slices: 4A (current-school/membership
authorization foundation — **done**), 4B (plain-CRUD query/object/form
scoping), 4C (Lesson/scheduling subsystem scoping), 4D (remaining
`is_staff` cleanup + full regression/IDOR audit).

Every authenticated principal must operate inside their own school
context. Phase 4A establishes *whose* context that is; Phases 4B–4D
make every view/service/query actually respect it.

## Phase 4A — Current-school and membership-access foundation (done)

- [x] Resolve the current school from the authenticated user's
      SchoolMembership.
- [x] Never trust a client-supplied school ID — `CurrentSchoolService`
      re-validates every session-stored id, and every selection,
      against a live, `role=PRINCIPAL` `SchoolMembership` row.
- [x] Establish a consistent way for views to obtain the current school
      (`SchoolAccessRequiredMixin` → `self.current_school`).
- [x] Auto-select the current school when the user has exactly one
      membership.
- [x] Send a user with multiple memberships and nothing (validly)
      selected to a minimal school-selection page
      (`ChooseSchoolView`, `/choose-school/`).
- [x] Reject selection of a school the user does not belong to, and of
      a nonexistent school id.
- [x] A membership removed while its school is the session's current
      selection stops granting access on the very next request (no
      caching of the authorization decision).
- [x] Zero-membership users get a simple "no school access" page
      instead of a 500 or a silent administrator fallback.
- [x] `is_staff`/`is_superuser` play no role in this decision anywhere
      — replaced the `is_staff`-based `AdministratorRequiredMixin` with
      `SchoolAccessRequiredMixin` on every view that used it
      (`SchedulerListView`/`CreateView`/`UpdateView`/`DeleteView` and
      their Teacher/Room/Subject/StudentGroup/AcademicYear/Period/
      Lesson subclasses, `StaffScheduleView`, `TeacherSubstitutionView`,
      `GeneratePlannedSubstitutionsView`). A superuser with no
      membership is denied; a non-staff user with a PRINCIPAL
      membership is allowed.

Deliberately NOT done in 4A (see 4B/4C below): no queryset, form
choice, or object lookup is scoped by school yet. `ScheduleView`'s
`is_staff` checks and all `is_staff` checks in templates/`navigation.py`
are untouched. Django Admin is untouched (see §24 of
`PROJECT_CONTEXT.md`).

## Phase 4B — Plain-CRUD query/object/form scoping (not started)

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

Generic Django views must not allow a principal to manipulate an
object belonging to another school by guessing its primary key.

- [ ] Audit and scope UpdateViews' `get_queryset()`.
- [ ] Audit and scope DeleteViews' `get_queryset()`.
- [ ] Audit CreateViews — force-assign `school` server-side instead of
      exposing it as a client-choosable form field.
- [ ] Audit custom `get_object()` calls.
- [ ] Add tests for cross-school access (404 on another school's id).

ModelChoiceFields must not expose objects belonging to another school.

- [ ] AcademicYear choices scoped (`PeriodForm`).
- [ ] Teacher/Room/Subject/StudentGroup/Period choices scoped
      (`LessonForm`).

## Phase 4C — Lesson/scheduling subsystem scoping (not started)

- [ ] Lesson queries scoped through AcademicYear/School.
- [ ] Substitute-teacher queries scoped by School.
- [ ] Schedule queries scoped by School.
- [ ] `ScheduleView`/`StaffScheduleView`/`TeacherSubstitutionView`/
      `GeneratePlannedSubstitutionsView` validate any user-suppliable
      `academic_year`/resource id against the current school (closes
      the cross-tenant timetable disclosure found during the Phase 4
      inspection).
- [ ] `DjangoLessonRepository`/`ScheduleService`/`SubstitutionService`/
      `ConflictService` reject a school/academic-year mismatch
      independent of the view layer.

## Phase 4D — Cleanup and full audit (not started)

- [ ] Replace remaining `is_staff` checks in `schedule.html` and
      `navigation.py` that gate business features (not Django Admin)
      with current-school/membership checks.
- [ ] Full IDOR/security audit sweep against the Phase 4 inspection
      checklist.
- [ ] Full regression pass.

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

- [ ] Ensure lessons are accessible only within the current school
      (needs Phase 4's current-school resolution; not done).
- [x] Validate that the lesson's teacher belongs to the same school.
- [x] Validate that the lesson's room belongs to the same school.
- [x] Validate that the lesson's subject belongs to the same school.
- [x] Validate that the lesson's student group belongs to the same
      school.
- [x] Validate that the lesson's Period belongs to the same school.
- [x] Prevent cross-school references.
- [x] Add appropriate tests.

  Implemented in Phase 3 as a narrow data-integrity guard
  (`CrossSchoolLessonError`, raised by
  `ScheduleService._ensure_same_school()`), pulled forward because
  giving these resources a `school` FK is what first made a
  cross-school Lesson possible. This is not the full lesson/scheduling
  access-control system: the Lesson form's dropdowns are still unscoped
  and `planned_substitute` is not checked against this invariant.

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

- [x] Ensure teacher pool is limited to the current school.
- [x] Ensure substitute assignments cannot cross schools.
- [x] Audit `list_teachers()`.
- [x] Audit `SubstitutionService`.
- [x] Audit substitution-related repository methods.
- [x] Add two-school isolation tests.

  Implemented in Phase 3: `list_teachers()` now requires a `school_id`
  and only returns that school's teachers; `SubstitutionService`
  (`available_teachers`, `generate_planned_substitutions`,
  `generate_plan`) and `ScheduleService.staff_schedule` resolve the
  school from the `academic_year_id` they already receive via a new
  `get_academic_year_school_id()` repository method, so their own
  public signatures didn't need to change. This is a repository/service
  *contract* change, not the full Phase 4 authorization system — there
  is still no current-school resolution, so a caller could still pass
  an arbitrary `academic_year_id`.

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

Phases 1–3 (School/SchoolMembership foundation, AcademicYear ownership,
Teacher/Room/Subject/StudentGroup ownership) are implemented, verified,
and committed. Phase 4A (current-school and membership-access
foundation) is implemented and verified, and not yet committed. The
existing "principal" user still has not been attached to a school —
`create_school` remains written but intentionally not run. The real dev
database is migrated through `0012`; no migration was needed for
Phase 4A.

## Immediate next step

1. Review the diff for the Phase 4A slice.
2. Decide whether/when to run `create_school` against the dev database.
3. Commit.
4. Move to Phase 4B (plain-CRUD query/object/form scoping — see the
   Phase 4 section above).

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
      for defense-in-depth (Phase 3 answered this narrowly for Lesson:
      no FK added; a `CrossSchoolLessonError` application-layer check
      is used instead — see the Phase 6 notes above. Still open for
      Period/Lesson more broadly).
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

## 2026-09-17 (continued) — Phase 2: AcademicYear → School

### Completed

- Added `AcademicYear.school` as a required `ForeignKey` to `School`
  (`on_delete=CASCADE`), replaced the global `unique=True` on `name`
  with a `UniqueConstraint(school, name)`, updated `Meta.ordering` to
  `["school", "-name"]`, and changed `__str__` to
  `f"{self.name} ({self.school})"` for disambiguation.
- Split the schema change into three migrations, per the documented
  strategy (§22 of `PROJECT_CONTEXT.md`):
  - `0007_academicyear_school_nullable` — add `school`, nullable.
  - `0008_backfill_academicyear_school` — `RunPython` data migration:
    any `AcademicYear` with no school is assigned to a `get_or_create`d
    "Default School".
  - `0009_academicyear_school_required` — make `school` required, swap
    the uniqueness constraint.
- Updated `AcademicYearForm` to expose `school` as a field (unscoped —
  lists all schools; scoping is Phase 4), otherwise the create/update
  views would fail to save.
- Updated `AcademicYearListView` and `AcademicYearAdmin` to show/filter
  by `school`.
- Updated `load_demo_data._load_academic_year()` to `get_or_create` a
  "Demo School" when creating a fresh AcademicYear (only affects a
  brand-new database — on the real dev DB the existing AcademicYear is
  reused as before).
- Confirmed `ScheduleService`, `ConflictService`, `SubstitutionService`,
  and `DjangoLessonRepository` need no changes — they only ever handle
  an opaque `academic_year_id`.
- Updated every existing `AcademicYear.objects.create(...)` call across
  5 test files (~15 call sites) to pass an explicit `school=`.
- Added `tests/infrastructure/test_academic_year_school.py` (required
  FK, per-school uniqueness, cross-school duplicate names allowed,
  cascade delete, `__str__` format) and
  `tests/integration/test_academic_year_school_migration.py` (tests the
  `0008` data migration itself via Django's `MigrationExecutor` against
  historical model states — single and multiple orphaned rows).
- Added 3 new web tests covering `AcademicYearForm`/`AcademicYearCreateView`
  with the new required `school` field, and the list view's School column.
- Verification performed:
  - `makemigrations --check --dry-run` → no changes detected.
  - `manage.py check` → no issues.
  - Full pytest suite → 130 passed, 1 pre-existing failure unrelated to
    this change (`test_administrator_navigation`, same failure present
    on the base branch before Phase 1/2 work).
  - Applied `0006`–`0009` to the real dev `db.sqlite3` (a backup was
    taken beforehand and removed after verifying success). Confirmed
    afterward: 1 `School` ("Default School"), the existing "Demo 2026"
    `AcademicYear` now owned by it, and Teacher/Room/Subject/
    StudentGroup/Lesson counts unchanged (80/42/10/42/2100).
- No changes made to Teacher, Room, Subject, StudentGroup, Lesson,
  repositories, services, or authentication/authorization logic.

### Current task

Phase 1 and Phase 2 are both implemented and verified but not committed.

### Next

Review the diff, decide on committing, then move to Phase 3 (connect
Teacher, Room, Subject, and StudentGroup to School).

## 2026-09-18 — Phase 3: School-owned resources

### Completed

- Added `school` as a required `ForeignKey` to School (`on_delete=CASCADE`)
  on `Teacher`, `Room`, `Subject`, and `StudentGroup`; replaced each
  model's global `unique=True` on `name` with a per-school
  `UniqueConstraint(school, name)`; set `Meta.ordering = ["school", "name"]`
  for all four. Left `Subject.code` untouched (no uniqueness existed
  before, none added).
- Split the schema change into three migrations, mirroring Phase 2's
  strategy but bundled across all four models so the backfill assigns
  them to one reused School:
  - `0010_school_owned_resources_nullable` — add `school` (nullable) to
    all four models.
  - `0011_backfill_school_owned_resources` — `RunPython`: reuses (via
    `get_or_create(name="Default School")`) the exact same "Default
    School" Phase 2's `0008` already created, then bulk-assigns any
    orphaned rows in all four models to it.
  - `0012_school_owned_resources_required` — make `school` required,
    drop `name`'s field-level uniqueness, add the per-school
    `UniqueConstraint`s, set the new ordering.
- Added a narrow Lesson-resource cross-school integrity guard (a slice
  of Phase 6, pulled forward — see the Phase 6 notes above): a new
  `CrossSchoolLessonError` domain exception; `ResourceSchoolIds` and
  `get_resource_school_ids()`/`get_academic_year_school_id()` added to
  the `LessonRepository` protocol and its Django implementation;
  `ScheduleService._ensure_same_school()` calls it from both
  `create_lesson()` and `update_lesson()`; `LessonWriteMixin` in
  `views.py` catches it as a non-field form error. Explicitly does not
  add a `school` FK to `Lesson`, does not check `planned_substitute`
  against this invariant, and does not scope the Lesson form's
  dropdowns (all deliberately out of scope).
- Scoped `list_teachers()` by school (a slice of Phase 7, pulled
  forward — see the Phase 7 notes above): its signature now requires
  `school_id`; `SubstitutionService.available_teachers()`,
  `.generate_planned_substitutions()`, `.generate_plan()`, and
  `ScheduleService.staff_schedule()` resolve the school via the new
  `get_academic_year_school_id()` from the `academic_year_id` they
  already receive, so none of their own public signatures (or their
  view/demo-data callers) needed to change.
- Updated `TeacherForm`/`RoomForm`/`SubjectForm`/`StudentGroupForm` to
  include `school` (unscoped, same treatment as `AcademicYearForm`);
  updated the four list views' `columns` and the four `ModelAdmin`s to
  show/filter by `school`.
- Updated `load_demo_data` to thread the demo AcademicYear's `school`
  through teacher/room/subject/student-group creation and lookup.
- Updated every existing `Teacher/Room/Subject/StudentGroup.objects.create(...)`
  call across 7 test files to pass an explicit `school=`.
- Added `tests/infrastructure/test_resource_school_ownership.py`
  (required FK, per-school uniqueness, cross-school duplicate names
  allowed, cascade delete, and `ProtectedError` when a resource is still
  referenced by a Lesson — parametrized across all four models),
  `tests/integration/test_school_owned_resources_migration.py` (the
  `0011` backfill via `MigrationExecutor`, including the real-dev-DB
  scenario of an already-existing "Default School" being reused rather
  than duplicated), `tests/integration/test_lesson_school_integrity.py`
  (real-DB `CrossSchoolLessonError` coverage for all four resource
  types, both create and update), a real-DB `list_teachers()` isolation
  test in `tests/infrastructure/test_django_lesson_conflicts.py`, new
  fake-repository isolation tests in `test_schedule_service.py` and
  `test_substitution_service.py`, and a web-level test confirming the
  Lesson form surfaces the cross-school error as a non-field error.
- Verification performed:
  - `makemigrations --check --dry-run` → no changes detected.
  - `manage.py check` → no issues.
  - Full pytest suite → 162 passed, 1 pre-existing failure unrelated to
    this change (`test_administrator_navigation`; confirmed it also
    fails on the pre-Phase-3 code via `git stash`).
  - Applied `0010`–`0012` to the real dev `db.sqlite3` (a backup was
    taken beforehand and removed after verifying success). Confirmed
    afterward: still 1 `School` ("Default School"), Teacher/Room/
    Subject/StudentGroup/Lesson counts unchanged (80/42/10/42/2100), all
    four resource models owned solely by "Default School", and zero
    Lessons found combining resources from different schools.
- No changes to `Lesson` (no `school` FK added), no domain-layer
  `school_id` added to the domain `Teacher` dataclass, and no Phase 4
  authentication/current-school system or Phase 9 multi-school demo
  redesign implemented.

### Current task

Phase 1, Phase 2, and Phase 3 were implemented and verified, and have
since been committed (`6f15813`, `c3202eb`, `4a29142`).

### Next

Move to Phase 4 (School data isolation), starting with the 4A
current-school/authorization foundation.

## 2026-09-19 — Phase 4A: Current-school and membership-access foundation

### Completed

- Added `app/presentation/web/school_access.py`:
  - `CURRENT_SCHOOL_SESSION_KEY` — the one named session-key constant
    used everywhere (no scattered string literals).
  - `CurrentSchoolService.memberships_for(user)` — a user's
    `role=PRINCIPAL` `SchoolMembership` rows.
  - `CurrentSchoolService.resolve(request)` — re-validates any
    session-stored school id against a live membership, discarding it
    (never trusting it) if invalid; auto-selects when the user has
    exactly one membership; returns `None` when the choice is
    ambiguous or there is none.
  - `CurrentSchoolService.set_current(request, school_id)` — the only
    way to change the session value; validates the id (including
    non-numeric/garbage input) against the user's own memberships
    first and changes nothing on failure.
  - `SchoolAccessRequiredMixin(LoginRequiredMixin)` — requires login,
    resolves the current school via the service above, exposes it as
    `self.current_school`, redirects to `ChooseSchoolView` when
    multiple memberships are unresolved, and renders a minimal
    "no school access" page (403) otherwise. Does not consult
    `is_staff`/`is_superuser` at all.
  - No repository/protocol abstraction was introduced — this talks to
    `SchoolMembership`/`School` directly via the ORM, the same way the
    existing plain-CRUD views already do; only the Lesson/scheduling
    subsystem has the full ports/repository treatment in this
    codebase, and this isn't part of that subsystem.
- Replaced `AdministratorRequiredMixin` (the sole `is_staff`-based gate)
  with `SchoolAccessRequiredMixin` everywhere it was used in
  `app/presentation/web/views.py`: `SchedulerListView`,
  `SchedulerCreateView`, `SchedulerUpdateView`, `SchedulerDeleteView`
  (and therefore every Teacher/Room/Subject/StudentGroup/AcademicYear/
  Period/Lesson CRUD view built on them), `GeneratePlannedSubstitutionsView`,
  `StaffScheduleView`, `TeacherSubstitutionView`.
- Added `ChooseSchoolView` (`views.py`) — GET lists only the requesting
  user's own memberships (never `School.objects.all()`); POST validates
  the submitted `school_id` via `CurrentSchoolService.set_current()`
  and redirects to `schedule` on success or re-renders with a 400 and
  an error message on failure (foreign or nonexistent id). Also
  degrades sensibly on direct navigation with zero or exactly one
  membership.
- Added URL `choose-school/` → `ChooseSchoolView` in
  `app/presentation/web/urls.py`.
- Added two minimal templates:
  `scheduler/choose_school.html` (a school-per-radio-button form) and
  `scheduler/no_school_access.html` (a short explanatory page).
- Updated `tests/integration/test_web_pages.py`'s `authenticated_client`
  fixture to also create a `School` + `SchoolMembership(PRINCIPAL)` for
  its superuser — this fixture is used throughout that file as "the
  administrator," and superusers no longer bypass school-membership
  checks (by design), so it needed a membership to keep exercising the
  same views.
- Added `tests/conftest.py` with three small factory fixtures
  (`make_user`, `make_school`, `make_membership`) — the first shared
  fixture module in the test suite, justified by genuine reuse across
  the new Phase 4A tests (and expected reuse in 4B/4C).
- Added `tests/integration/test_current_school_access.py` (13 tests):
  single-membership auto-selection; multi-membership redirect to
  `choose-school`; selecting a valid membership (and that it lands in
  the session); rejecting a school the user doesn't belong to;
  rejecting a nonexistent school id; access stopping immediately after
  a membership is deleted; the zero-membership "no school access"
  response; `is_staff=True`-without-membership denied; non-staff
  PRINCIPAL-membership allowed; superuser-without-membership denied;
  superuser-with-membership allowed; and an explicit test that a
  tampered/foreign session value is discarded in favor of the database
  truth rather than trusted.
- Verification performed:
  - `manage.py check` → no issues.
  - `makemigrations --check --dry-run` → no changes detected (no
    schema change was needed for Phase 4A).
  - Full pytest suite → 175 passed, 1 pre-existing failure unrelated to
    this change (`test_administrator_navigation`, same failure present
    before Phase 4A).
- Explicitly NOT done (deferred to 4B/4C/4D, per scope): no queryset,
  `ModelChoiceField`, or object lookup was scoped by school; `school`
  is still a client-choosable field on the four resource forms and
  `AcademicYearForm`; `ScheduleView`'s `is_staff` checks and all
  `is_staff` checks in `schedule.html`/`navigation.py` are untouched;
  Django Admin is untouched. No migration, no new `SchoolMembership`
  role, no registration/invitation/onboarding work.

### Current task

Phase 4A is implemented and verified but not committed.

### Next

Review the diff, decide on committing, then move to Phase 4B (plain-CRUD
query/object/form scoping).
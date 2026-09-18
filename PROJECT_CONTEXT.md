# School Scheduler — Project Context

## 1. Project Overview

School Scheduler is a Django-based web application for managing school
timetables and substitute teachers.

The original application was designed around a single school.

The long-term goal is to turn it into a multi-school application that
could be used by real schools and principals.

The application should eventually allow a principal to:

- register/login;
- create and manage a school;
- create academic years;
- configure the timetable structure;
- manage teachers;
- manage rooms;
- manage subjects;
- manage student groups/classes;
- create and manage lessons;
- generate and manage substitute-teacher assignments;
- view schedules;
- operate without access to another school's data.

The application is currently a local development project and is not yet
deployed publicly.

---

# 2. Main Learning Goal

This project is also being used as a learning project.

The developer wants to understand:

- Python;
- Django;
- HTTP and web application flow;
- databases and SQL;
- Django ORM;
- authentication and authorization;
- application architecture;
- repositories and services;
- testing;
- Git;
- deployment;
- how to use AI coding agents effectively.

AI tools such as Claude Code and ChatGPT should be used as development
collaborators, not as black-box code generators.

The goal is not simply to make the application work.

The goal is to understand why the application works and to be able to
read, debug, modify, and extend it independently.

---

# 3. Technology

Current technology includes:

- Python
- Django
- SQLite for local development
- pytest / Django testing
- Git
- HTML/CSS/templates
- Django ORM

The exact dependencies are listed in:

    requirements.txt

Do not introduce additional technologies unless there is a clear
reason to do so.

---

# 4. Project Structure

The project currently has approximately this structure:

    school_scheduler_codex/
    ├── app/
    │   ├── domain/
    │   │   └── policies.py
    │   ├── infrastructure/
    │   ├── management/
    │   ├── migrations/
    │   ├── presentation/
    │   ├── templatetags/
    │   ├── models.py
    │   ├── admin.py
    │   └── apps.py
    ├── config/
    ├── tests/
    ├── docs/
    │   └── screenshots/
    ├── db.sqlite3
    ├── manage.py
    ├── PROJECT_BLUEPRINT.md
    ├── PROJECT_CONTEXT.md
    ├── PROJECT_ROADMAP.md
    ├── README.md
    ├── structure.txt
    └── requirements.txt

The actual repository structure is the source of truth. This document
describes the architecture conceptually and may become outdated as the
project evolves.

---

# 5. Architecture

The application uses a simplified Clean Architecture / Hexagonal
Architecture approach.

Conceptually:

    Presentation
        ↓
    Application
        ↓
    Ports / Interfaces
        ↓
    Infrastructure
        ↓
    Django ORM / Database

More specifically:

    Django views/forms/templates
            ↓
    Application services
            ↓
    LessonRepository interface
            ↑
    DjangoLessonRepository
            ↓
    Django ORM models
            ↓
    Database

The domain layer should remain independent of Django whenever
practical.

---

# 6. Domain Layer

The domain layer contains framework-independent business concepts and
rules.

Examples include:

- Day
- PeriodKind
- Teacher
- Period
- Lesson

The domain models are implemented using Python dataclasses and should
not depend directly on Django ORM models.

For example, the domain contains concepts such as:

    Teacher
    Period
    Lesson

The domain layer is intended to represent business concepts rather
than database implementation details.

---

# 7. Current Domain Concepts

## Day

The scheduling system currently supports:

- Monday
- Tuesday
- Wednesday
- Thursday
- Friday

## PeriodKind

There are currently two types:

- LESSON
- BREAK

## Teacher

The domain Teacher contains:

- id
- name
- email

## Period

A Period contains:

- id
- academic_year_id
- name
- order
- start_time
- end_time
- kind

Period validation currently includes:

- start time must be before end time;
- order must be at least 1.

A Period can accept lessons only when its kind is LESSON.

## Lesson

A Lesson contains:

- teacher_id
- subject_id
- room_id
- student_group_id
- day
- start_period_id
- planned_substitute_id
- notes
- id

---

# 8. Current Django Models

The main Django persistence models are located in:

    app/infrastructure/database/models.py

The current models include:

- School
- SchoolMembership
- AcademicYear
- Teacher
- Room
- Subject
- StudentGroup
- Period
- Lesson

`AcademicYear`, `Teacher`, `Room`, `Subject`, and `StudentGroup` are all
connected to `School` via required foreign keys (see §10 and §15).

---

# 9. Current Database Relationships

The current conceptual structure is approximately:

    School
        ├── AcademicYear
        │       │
        │       └── Period
        ├── Teacher
        ├── Room
        ├── Subject
        └── StudentGroup

    Lesson
        ├── Teacher
        ├── Subject
        ├── Room
        ├── StudentGroup
        ├── Period
        └── planned substitute Teacher

`School` and `SchoolMembership` exist (see §11–§12). `AcademicYear`,
`Teacher`, `Room`, `Subject`, and `StudentGroup` all have a required
foreign key to `School` (see §10 and §15). `Lesson` still has no
`school` foreign key of its own — see §17 for how its consistency with
one School is now enforced instead.

---

# 10. AcademicYear

AcademicYear currently contains:

- school (ForeignKey to School, required, `on_delete=CASCADE`)
- name
- default_period_duration

`name` is no longer globally unique. It is unique per School via a
`UniqueConstraint(fields=["school", "name"])`. Different schools can
have AcademicYears with the same name:

    School A → Academic Year 2026
    School B → Academic Year 2026

is valid.

`AcademicYear.__str__()` returns `f"{self.name} ({self.school})"` so
that same-named AcademicYears from different schools remain
distinguishable in the admin, dropdowns, and templates.

No school-scoping/authorization exists yet for AcademicYear access —
the `AcademicYearForm`'s `school` field currently lists every School
unscoped. Restricting it to the authenticated principal's school is
Phase 4.

---

# 11. School

`School` now exists as a Django model
(`app/infrastructure/database/models.py`). It is the tenancy root of
the application.

Current fields: `name` (CharField, intentionally NOT globally unique —
real schools can share a name) and `created_at`.

`AcademicYear`, `Teacher`, `Room`, `Subject`, and `StudentGroup` all
have a required `school` foreign key (Phase 2 and Phase 3 of the
roadmap, both implemented — see §10 and §15).

The future architecture is:

    User
      │
      └── SchoolMembership
                │
                └── School
                      │
                      ├── AcademicYear
                      │      └── Period
                      │
                      ├── Teacher
                      ├── Room
                      ├── Subject
                      └── StudentGroup

Lessons will belong indirectly to a School through their AcademicYear
and associated resources.

A School should isolate all of its data from every other School.

---

# 12. Principal / User

The current application uses Django's built-in `User` model (no custom
`AUTH_USER_MODEL`) and `is_staff` for some authentication/admin-related
behavior.

A dedicated membership model now exists: `SchoolMembership`
(`app/infrastructure/database/models.py`), connecting a `User` to a
`School`:

    Django User
         │
         └── SchoolMembership (role, currently only "PRINCIPAL")
                    │
                    └── School

`SchoolMembership` is a join model — `(user, school)` is unique, but a
`User` can belong to multiple `School`s and a `School` can have
multiple members, via separate `SchoolMembership` rows.

Current-school resolution now exists (Phase 4A —
`app/presentation/web/school_access.py`). `CurrentSchoolService` is a
small, session-based helper (no repository/protocol layer — this is
plain-CRUD-shaped logic, the same category as the existing Teacher/
Room/Subject/StudentGroup/AcademicYear views, not the Lesson/scheduling
subsystem):

- The session stores only a `current_school_id` *hint*
  (`CURRENT_SCHOOL_SESSION_KEY`, defined once as a constant). It is
  never treated as proof of access.
- `CurrentSchoolService.resolve(request)` re-validates that hint (or
  auto-selects when the user has exactly one `SchoolMembership`) against
  a live, `role=PRINCIPAL` `SchoolMembership` query on every call — a
  membership revoked mid-session, or a session value that never
  corresponded to a real membership, is discarded rather than trusted,
  and access stops on the very next request.
- `CurrentSchoolService.set_current(request, school_id)` is the only
  way to change the session value, and only succeeds if the requesting
  user actually holds a `PRINCIPAL` `SchoolMembership` for that
  `school_id`; a foreign or nonexistent id changes nothing and returns
  `None`.
- `SchoolAccessRequiredMixin` (replacing the old `AdministratorRequiredMixin`)
  requires login, resolves the current school via the service above, and
  exposes it as `self.current_school`. Zero memberships renders a
  minimal "no school access" page (403); multiple memberships with
  nothing validly selected redirect to a minimal `ChooseSchoolView`
  (`/choose-school/`) that only ever lists — and only ever accepts — the
  requesting user's own memberships.
- This mixin now gates every view that used to check `is_staff`
  (`SchedulerListView`/`CreateView`/`UpdateView`/`DeleteView` and their
  Teacher/Room/Subject/StudentGroup/AcademicYear/Period/Lesson
  subclasses, `StaffScheduleView`, `TeacherSubstitutionView`,
  `GeneratePlannedSubstitutionsView`). `is_staff`/`is_superuser` play no
  role in this decision at all — a superuser with no `SchoolMembership`
  is denied exactly like anyone else; a non-staff user with a
  `PRINCIPAL` membership is allowed.

**Phase 4A scope note**: this establishes *who may act as which
school* and gives every gated view a trustworthy `self.current_school`.
It deliberately does **not** yet scope any queryset, form choice, or
object lookup by that school — a Teacher/Room/Lesson list view still
returns every school's rows, and Create/Update views still don't force
resources onto `self.current_school`. That queryset/object/form scoping
is Phase 4B. The `ScheduleView` (public timetable) and its `is_staff`
checks, and all remaining `is_staff` checks in templates
(`schedule.html`, `navigation.py`), are also untouched — those are
Phase 4B–4D work.

A `create_school` management command exists to create a `School` and
attach an existing `User` to it as a principal
(`app/management/commands/create_school.py`). It has not been run
against the development database yet.

The important architectural decision is:

`is_staff` should NOT be used as the application's concept of school
ownership. This is now enforced in code (§ above), not just an
intention: `is_staff`/`is_superuser` are reserved for Django Admin
access only (see §24) and are never consulted by
`SchoolAccessRequiredMixin` or `CurrentSchoolService`.

A user being a Django staff user and a user being a principal/member of
a particular school are separate concepts.

The application should eventually support multiple staff/users for the
same school.

---

# 13. School Data Isolation

School isolation is one of the most important requirements of the
multi-school architecture.

A principal from School A must never be able to:

- see School B's teachers;
- see School B's rooms;
- see School B's subjects;
- see School B's student groups;
- see School B's academic years;
- see School B's lessons;
- modify School B's data;
- delete School B's data;
- assign School B's teachers to School A lessons;
- otherwise access School B's private data.

The application must not rely on the browser/client to provide a valid
school ID.

The current school should be determined from the authenticated user's
Principal/membership.

**Phase 4B implemented this for all CRUD operations** on Teacher, Room,
Subject, StudentGroup, AcademicYear, Period, and Lesson — see §14 for
the mechanism.

**Phase 4C implemented this for the scheduling subsystem**:
`ScheduleView` (for authenticated users with a resolvable current
school — see below), `StaffScheduleView`, `TeacherSubstitutionForm`/
`TeacherSubstitutionView`, and `GeneratePlannedSubstitutionsView`.

---

# 14. IDOR / Object Access Security

A particularly important security concern is insecure direct object
reference (IDOR).

For example, an authenticated user should not be able to access another
school's object simply by changing:

    /teachers/15/

to:

    /teachers/16/

if teacher 16 belongs to another school.

Object retrieval must therefore be scoped to the current school.

Avoid unsafe patterns such as:

    Model.objects.get(pk=some_id)

when the object belongs to a school-owned resource.

Instead, access should be constrained by the authenticated user's
school.

This applies to:

- detail views;
- update views;
- delete views;
- custom object lookups;
- repositories;
- services;
- forms.

**Phase 4B implementation** (`app/presentation/web/views.py`,
`app/presentation/web/forms.py`): CRUD isolation for Teacher, Room,
Subject, StudentGroup, AcademicYear, Period, and Lesson is done and
tested. The scheduling-subsystem views (`ScheduleView`,
`StaffScheduleView`, `TeacherSubstitutionView`,
`GeneratePlannedSubstitutionsView`) and `DjangoLessonRepository`/
`ScheduleService`/`SubstitutionService` beyond what Phase 3 already
added are untouched — that is Phase 4C.

- **List isolation** — `SchoolScopedQuerysetMixin`, a small mixin with
  one `school_filter_lookup` class attribute (default `"school"`,
  overridden to `"academic_year__school"` for Period or
  `"start_period__academic_year__school"` for Lesson) and one
  `get_queryset()` method that filters by
  `self.current_school`. Applied to `SchedulerListView`,
  `SchedulerUpdateView`, and `SchedulerDeleteView` — the three shared
  bases behind every Teacher/Room/Subject/StudentGroup/AcademicYear/
  Period/Lesson CRUD view.
- **Update/Delete IDOR protection** — the same mixin, for free: Django's
  `SingleObjectMixin.get_object()` builds itself from `get_queryset()`,
  so a pk belonging to another school simply isn't in the filtered
  queryset and 404s instead of being returned, edited, or deleted.
- **Create school assignment** — `school` was removed entirely from
  `TeacherForm`/`RoomForm`/`SubjectForm`/`StudentGroupForm`/
  `AcademicYearForm`'s `Meta.fields` (it is never a client-choosable
  field for these five models). `SchedulerCreateView` gained an
  `assign_current_school` flag (`True` on those five Create views only)
  and a `get_form()` override that sets `form.instance.school =
  self.current_school` — deliberately in `get_form()`, not
  `form_valid()`, because `ModelForm.validate_unique()` runs during
  `form.is_valid()`, before `form_valid()` is ever called.
- **A real bug this caught**: removing `school` from `Meta.fields` makes
  Django's own `_get_validation_exclusions()` exclude `school` from
  `validate_unique()` entirely (Django excludes any field not present
  on the form), which silently skips the per-school
  `UniqueConstraint(school, name)` check and lets a duplicate name
  reach the database as a raw `IntegrityError` instead of a form error.
  Fixed with a small, targeted override of
  `_get_validation_exclusions()` on `BaseStyledModelForm`: if `school`
  would be excluded but the instance already has one set (i.e. the view
  assigned it), keep it in the check. Caught by
  `test_create_enforces_per_school_name_uniqueness` during
  implementation, not discovered later.
- **Form queryset isolation** — `BaseStyledModelForm.__init__` now
  accepts (and, for forms that don't need it, silently ignores) a
  `school=None` keyword. `SchedulerCreateView`/`SchedulerUpdateView`
  both inject `school=self.current_school` via `get_form_kwargs()`
  unconditionally; only `PeriodForm` (its `academic_year` field) and
  `LessonForm` (`teacher`, `planned_substitute`, `subject`, `room`,
  `student_group`, `start_period`) actually use it, scoping every one
  of those `ModelChoiceField`s to `Model.objects.filter(school=school)`
  (or `academic_year__school=school` for `start_period`). Choosing
  `.filter(school=school)` rather than a `.objects.all()` fallback
  means a missing/forgotten `school` — a bug, not a normal path — fails
  *closed* (zero choices) rather than reopening the vulnerability.
- **Lesson vs. Phase 3**: Phase 3's `CrossSchoolLessonError` guard (are
  a Lesson's own resources mutually consistent with each other?) is
  unmodified and still tested by
  `tests/integration/test_lesson_school_integrity.py`. Phase 4B adds a
  different, narrower question — are they consistent with *my* current
  school? — enforced at the form level. In practice, once `LessonForm`'s
  fields are scoped, `cleaned_data` can only ever contain
  `current_school` resources, so Phase 3's guard is no longer the thing
  that catches a foreign id in the normal CRUD flow (Django's
  `ModelChoiceField` rejects it first, as a field-level "select a valid
  choice" error) — it remains a defense-in-depth safety net for any
  future caller that bypasses the form.

**Phase 4C implementation** (`app/presentation/web/views.py`,
`app/presentation/web/forms.py`, `app/presentation/web/school_access.py`,
`app/domain/exceptions.py`, `app/application/services/substitution_service.py`):
closes the scheduling-subsystem gaps Phase 4B deliberately left open.
No repository or `ScheduleService`/`ConflictService` change was needed
— every fix is presentation-layer, using the same direct-ORM scoping
pattern as Phase 4B, plus one narrow service-layer guard.

- **`GeneratePlannedSubstitutionsView`** — the POSTed `academic_year`
  id was trusted outright, letting a principal trigger a bulk
  `planned_substitute` mutation on another school's lessons (the
  highest-severity finding: authorization was completely absent even
  though Phase 3 already guaranteed the *teacher pool* used would
  correctly be that other school's own). Fixed by validating
  `AcademicYear.objects.filter(pk=..., school=self.current_school).exists()`
  before calling the service.
- **`StaffScheduleView`** — `academic_years = AcademicYear.objects.all()`
  was unscoped; a principal could view another school's entire staff
  schedule by `academic_year` id. Scoped to `self.current_school`;
  everything downstream (the `period`/`day` detail lookup) becomes safe
  automatically since it only operates on an already-scoped academic
  year. This view had no tests before Phase 4C.
- **`TeacherSubstitutionForm`** — `academic_year`/`period` were
  unscoped `ModelChoiceField`s (unlike `PeriodForm`/`LessonForm`, which
  Phase 4B already fixed). Given the same `school=None` fail-closed
  treatment; `TeacherSubstitutionView` now passes
  `school=self.current_school`. (Inspection also found this view has no
  POST/mutation path at all — it only shows which teachers are free for
  a given day/period; the risk was read-side disclosure, not mutation.)
- **`ScheduleView`** — `academic_years` and the teacher/room/
  student_group selector were fully unscoped, letting a logged-in
  principal view another school's whole timetable or per-resource
  schedule by id. This view is deliberately public (anonymous timetable
  viewing predates multi-school and is intentionally preserved — see
  §25), so the fix only applies *when a current school is resolvable*:
  `CurrentSchoolService.resolve(request)` is called directly (not via
  `SchoolAccessRequiredMixin`, which would incorrectly force login);
  anonymous visitors and authenticated users with no resolvable current
  school keep exactly today's global behaviour. `CurrentSchoolService.resolve()`
  gained an explicit `is_authenticated` guard as a prerequisite — every
  prior caller only ever invoked it post-login, so filtering
  `SchoolMembership` by an `AnonymousUser` had never been exercised and
  would have raised `ValueError`.
- **Narrow service-layer defense-in-depth** — a new `SchoolAuthorizationError`
  (`app/domain/exceptions.py`), distinct from `CrossSchoolLessonError`:
  the latter checks whether a lesson's components agree with *each
  other*, the former checks whether the *caller* is entitled to the
  school they agree on. Added only to
  `SubstitutionService.generate_planned_substitutions()` (an optional
  `school_id` parameter, validated against the academic year's actual
  school via the existing `get_academic_year_school_id()`) — the one
  method identified as bulk-mutating `Lesson.planned_substitute`
  directly from a view. `generate_plan()` is not reachable from any
  view and was deliberately left alone rather than guarded
  speculatively. The presentation-layer checks above remain the
  primary boundary; this is a backstop for a caller that reaches the
  service without going through them.

---

# 15. School-Owned Resources

`Teacher`, `Room`, `Subject`, and `StudentGroup` each belong directly to
a `School` (required `ForeignKey`, `on_delete=CASCADE`). This is
implemented, tested, and applied to the real development database.

These resources are reusable across academic years within the same
School — they belong to `School`, not `AcademicYear`.

The relationship is:

    School
       ├── Teachers
       ├── Rooms
       ├── Subjects
       └── StudentGroups

Each model's `name` is no longer globally unique. It is unique per
School via a `UniqueConstraint(fields=["school", "name"])`, replacing
the old field-level `unique=True`. For example:

    School A → Teacher "John Smith"
    School B → Teacher "John Smith"

is valid, while the same name twice within one School is rejected.
`Meta.ordering` is `["school", "name"]` for all four models.

`Subject.code` has no uniqueness constraint — it never did, and Phase 3
did not add one.

Deleting a School cascades to its Teachers/Rooms/Subjects/StudentGroups,
*unless* one of them is still referenced by a `Lesson` (`Lesson`'s
foreign keys to these models are `on_delete=PROTECT`), in which case the
deletion is blocked with `ProtectedError` — the same pattern already
used for `AcademicYear` → `Period` → `Lesson`.

`TeacherForm`, `RoomForm`, `SubjectForm`, and `StudentGroupForm` now
include `school` as a field (unscoped — lists every School; scoping the
choices to the authenticated principal's school is Phase 4, same as
`AcademicYearForm`). The corresponding list views and admin pages show
a School column/filter.

The `load_demo_data` command threads the demo AcademicYear's School
through teacher/room/subject/student-group creation, so demo data still
loads correctly; it does not yet generate more than one School's worth
of demo data (that richer multi-school demo redesign is still pending).

---

# 16. Periods

Periods belong to an AcademicYear.

The current Period model contains:

- academic_year
- name
- order
- start_time
- end_time
- kind

There are currently database constraints ensuring that:

- period order is unique within an AcademicYear;
- period name is unique within an AcademicYear.

Periods can represent:

- lesson periods;
- break periods.

The timetable configuration should eventually allow principals to
configure their school's periods, breaks, names, order, and times.

---

# 17. Lessons

Lessons currently reference:

- Teacher
- Subject
- Room
- StudentGroup
- Day
- Period
- planned substitute Teacher
- notes

A lesson does not have a direct School foreign key, and Phase 3
deliberately did not add one — the initial multi-school design avoids
unnecessary denormalized relationships.

Instead, `ScheduleService._ensure_same_school()` (called from both
`create_lesson()` and `update_lesson()`, before conflict checking) now
enforces that the Teacher, Subject, Room, and StudentGroup attached to a
Lesson all belong to the same School as the AcademicYear that owns the
Lesson's Period. It does this by asking the repository
(`LessonRepository.get_resource_school_ids()`) for each resource's
`school_id` and the Period's (via its AcademicYear) `school_id`, and
raising `CrossSchoolLessonError` (a new `DomainError`, not a subclass of
`InvalidLessonPlacementError`) if they don't all match. The domain layer
itself stays framework-independent — the school-id lookup lives in the
Django repository; only the comparison lives in the application-layer
service.

`LessonWriteMixin` (the Django view mixin backing the Lesson create/edit
forms) catches `CrossSchoolLessonError` and attaches it as a non-field
form error, the same way it already handles `ScheduleConflictError` and
`InvalidLessonPlacementError`.

This is a narrow data-integrity guard, not the full Phase 6 lesson/
scheduling access-control system: it does not scope the Lesson form's
ModelChoiceField querysets (a School A principal can still *see* School
B's teachers/rooms/etc. in the dropdowns until Phase 4), it does not
check the `planned_substitute` field against this invariant, and it does
not resolve an authenticated "current school" — it only rejects an
inconsistent combination once one is submitted.

---

# 18. Application Services

The application currently contains services such as:

- ScheduleService
- ConflictService
- SubstitutionService

These services contain application-level operations and business
workflows.

The exact implementation should be inspected in the repository before
making assumptions about behavior.

When adding multi-school support, services must not accidentally combine
data from different schools.

---

# 19. Repository Layer

The application uses a LessonRepository interface/Protocol
(`app/application/ports/repositories.py`), implemented by
`DjangoLessonRepository`.

`list_teachers()` now requires a `school_id` argument and only returns
Teachers belonging to that School (`Teacher.objects.filter(school_id=...)`).
Two supporting Protocol methods were added to make this possible without
requiring an authenticated "current school" (Phase 4 does not exist
yet): `get_academic_year_school_id(academic_year_id)` resolves an
AcademicYear to its owning School, and `get_resource_school_ids(...)`
resolves a would-be Lesson's Teacher/Room/Subject/StudentGroup/Period to
their School ids (used by the §17 cross-school lesson guard).

Every caller that previously called `list_teachers()` unscoped
(`SubstitutionService.available_teachers()`,
`.generate_planned_substitutions()`, `.generate_plan()`, and
`ScheduleService.staff_schedule()`) now resolves the relevant School via
`get_academic_year_school_id()` first. Their own public signatures are
unchanged — they still just take an `academic_year_id`, so no view or
demo-data call site needed to change.

This is a repository/service *contract* change, not the full Phase 4
authorization system: there is still no session-level "current school",
and nothing yet stops a view from calling these methods with an
arbitrary `academic_year_id`/`school_id`. What changed is that the
contract itself is now safe to wire up once Phase 4 resolves a current
school — it can no longer silently return every school's teachers.

---

# 20. Substitution Teacher Logic

The current intended substitution algorithm is:

1. For each lesson requiring a substitute, find teachers who are not
   teaching during that exact period.

2. Exclude teachers who are already assigned as substitutes during that
   period.

3. If candidates exist, choose among them using the teacher with the
   fewest existing substitution assignments.

4. If no candidates exist, expand the pool to teachers who are not
   teaching during that period even if they are already assigned as a
   substitute for another lesson during that period.

5. Again choose the teacher with the fewest existing substitution
   assignments.

This algorithm must operate only on teachers belonging to the current
school.

A teacher from another school must never appear in the candidate pool.
This is now enforced: `SubstitutionService` resolves the academic year's
School and passes it to `list_teachers(school_id)` before building the
candidate pool, so a teacher from a different School can no longer be
selected as a substitute — verified by fake-repository unit tests
(`tests/application/test_substitution_service.py`) and a real-database
repository test (`tests/infrastructure/test_django_lesson_conflicts.py`).

---

# 21. Current Single-School Assumptions

The current code contains several assumptions that work only because
there is effectively one school.

Resolved by Phase 2/3:

- globally unique Teacher/Room/Subject/StudentGroup/AcademicYear names
  (now per-school unique constraints);
- `list_teachers()` and the substitution/staff-schedule services
  returning every school's teachers (now scoped by school, see §19–20).

Still open (Phase 4+):

- unscoped repository queries for AcademicYear/Period/Lesson and the
  Lesson form's ModelChoiceFields (Teacher/Room/Subject/StudentGroup/
  Period/AcademicYear dropdowns still list every school's records);
- CRUD views querying all records (list views show every school's rows);
- schedule selection using globally available AcademicYears;
- demo data assuming one school (richer multi-school demo data is a
  later, separate redesign);
- no current-school context (no session/request-level "acting as School
  X" resolution exists yet).

These assumptions must be identified and removed carefully during the
multi-school transition.

Do not rewrite the entire application simply because these assumptions
exist.

Change them incrementally.

---

# 22. Migration Strategy

The application already contains existing data.

The multi-school migration should preserve that data.

A likely migration sequence is:

1. Add School model.
2. Add Principal/membership model.
3. Create a placeholder/default School for existing data.
4. Add nullable School foreign keys where required.
5. Backfill existing records.
6. Make School relationships required.
7. Replace global uniqueness with per-school uniqueness.
8. Update application code and forms.
9. Add isolation tests.

Existing users should not be guessed into a school automatically if
there is insufficient information.

User-to-school assignment may need to be performed manually or through
a management command.

---

# 23. Domain Architecture Decision

The domain layer should remain school-agnostic unless a specific
business rule requires School to be represented there.

School scoping can initially be enforced through:

- presentation;
- application services;
- repositories;
- persistence relationships.

Do not add `school_id` to every domain dataclass automatically.

Only introduce it when there is a clear domain-level reason.

---

# 24. Django Admin

Django Admin is currently part of the project.

For the initial multi-school implementation:

- Django Admin is primarily an administrative/development tool.
- It should not automatically become the principal's normal interface.
- Admin access should remain appropriately restricted.
- `is_staff` should remain separate from School membership.

Confirmed and unchanged by Phase 4A: Django Admin continues to use
Django's own `is_staff`/permission system exactly as before, with no
row-level School filtering. This is a deliberate, accepted MVP
constraint, not an oversight — retrofitting per-school row visibility
into every `ModelAdmin` (`get_queryset`, `has_change_permission`,
`formfield_for_foreignkey`) is real work the MVP doesn't need yet. The
operational rule this depends on: **ordinary principals must never be
granted `is_staff=True`** — doing so would give them full Django Admin
visibility into every school's data, bypassing the application-level
`SchoolAccessRequiredMixin`/`CurrentSchoolService` boundary entirely.
Nothing in the codebase currently prevents an operator from setting
`is_staff=True` on a principal's account by mistake; there is no
technical safeguard against it, only this documented rule.

A more sophisticated school-specific admin system can be designed later
if needed.

---

# 25. Public Timetable

A public timetable URL has not yet been finalized.

Eventually the application may support something like:

    School → public timetable

where parents/students can view timetable information without having
administrative access.

The exact URL structure and public/private information model should be
decided later.

Do not prematurely build the public timetable system.

**Phase 4C explicitly preserved today's interim behavior rather than
deciding this**: `ScheduleView` remains reachable by anyone, unscoped,
via `academic_year`/`teacher`/`room`/`student_group` query parameters —
exactly as it worked before multi-school. Phase 4C only added school
scoping for the *authenticated-principal* path (closing a real
cross-tenant disclosure for logged-in users), and treated this as
current-school authorization, not as a confidentiality boundary for
the public timetable. The open question above — what a real public
timetable's URL/access model should be — is unresolved and unrelated to
that fix.

---

# 26. Authentication Flow — Intended Future

The eventual registration flow should roughly be:

    User registers
          ↓
    Creates School
          ↓
    Principal / Membership created
          ↓
    User logs in
          ↓
    Application resolves current School
          ↓
    User manages only that School

Account creation and school creation should be handled safely, ideally
inside an appropriate database transaction.

---

# 27. Timetable Configuration — Intended Future

A principal should eventually be able to configure a timetable without
editing database records manually.

Possible configuration includes:

- number of periods;
- period names;
- lesson periods;
- breaks;
- start times;
- end times;
- default lesson duration.

The existing Period model already represents much of this information.

Avoid duplicating the same information in a separate configuration
system unless necessary.

---

# 28. Deployment

The application is currently local only.

The eventual goal is to deploy it so that it is accessible over the
Internet.

A possible deployment architecture is:

    Internet
        ↓
    Nginx
        ↓
    Gunicorn
        ↓
    Django
        ↓
    PostgreSQL

A VPS may host the application.

A single VPS can eventually host multiple small applications if its
resources are sufficient.

Deployment is itself an important learning objective, but deployment
should not distract from learning Django/backend development.

---

# 29. Development Workflow

The preferred development workflow is incremental.

For a significant feature:

1. Understand the current code.
2. Ask the AI agent to inspect the relevant files.
3. Ask for a plan before making major changes.
4. Review the plan.
5. Implement a small slice.
6. Review the diff.
7. Run tests.
8. Understand failures.
9. Fix problems.
10. Update project documentation.
11. Move to the next slice.

Do not ask the AI agent to implement the entire roadmap in one shot.

---

# 30. AI-Assisted Development

Claude Code and ChatGPT are being used together.

Claude Code can inspect and modify the repository.

ChatGPT can be used for:

- architecture discussion;
- reviewing Claude's plans;
- explaining code;
- debugging;
- evaluating design decisions;
- helping understand Django/Python concepts;
- planning implementation steps.

The developer should understand important changes before accepting them.

When learning something new, prefer:

    Think → Attempt → Ask AI → Understand → Implement → Test

rather than:

    Ask AI → Paste code → Hope it works

The purpose of the project is both to build software and to develop
real software-engineering ability.

---

# 31. Current Priority

The immediate priority is NOT to build every planned feature.

The immediate priority is to make the application multi-school
incrementally.

Recommended implementation order:

1. School model.
2. Principal / school membership.
3. AcademicYear → School.
4. School-owned resources.
5. School-scoped queries and views.
6. School-scoped lessons and scheduling.
7. School-scoped substitution.
8. Authentication/registration.
9. Demo data.
10. Full testing.
11. Production preparation.
12. Deployment.

Each step should be completed and tested before moving to the next major
step.

---

# 32. Important Constraints

- Do not break the existing scheduling algorithm unnecessarily.
- Do not rewrite the architecture without a concrete reason.
- Do not move business logic into Django views merely for convenience.
- Do not make the domain layer dependent on Django unless necessary.
- Do not trust client-supplied school IDs for authorization.
- Do not use global queries where school-scoped queries are required.
- Do not expose cross-school ModelChoiceField options.
- Do not assume primary-key secrecy provides authorization.
- Do not add unnecessary abstractions.
- Do not build features that are not currently needed.
- Do not mark roadmap items as completed merely because an AI agent
  proposed or planned them.
- A task is complete only when the relevant code has been implemented,
  tested, and verified.

---

# 33. Source of Truth

The repository itself is the ultimate source of truth.

This file provides architectural context.

`PROJECT_ROADMAP.md` tracks implementation progress.

`PROJECT_BLUEPRINT.md` contains the original project blueprint.

`README.md` describes the project for developers/users.

Git history records actual changes.

If these documents conflict with the actual code, inspect the code and
update the documentation rather than assuming the documentation is
correct.

---

# 34. Current Status

The project is currently transitioning from a single-school design to a
multi-school architecture.

The architecture and target relationships have been discussed and
defined conceptually.

The School + SchoolMembership foundation has been implemented (see
§11–§12): the `School` and `SchoolMembership` models, an additive
migration, admin registration, and a `create_school` management command
(not yet executed against the development database — the "principal"
user is not yet attached to a school).

`AcademicYear` now belongs to `School` (see §10): a required foreign
key, per-school unique names, and the three-migration nullable →
backfill → required sequence has been run against the real development
database. Its one existing AcademicYear ("Demo 2026") is now owned by
an auto-created "Default School".

`Teacher`, `Room`, `Subject`, and `StudentGroup` now belong to `School`
(see §15): required foreign keys, per-school unique names, the same
staged nullable → backfill → required migration sequence
(`0010`–`0012`), and forms/list-views/admin updated to expose/show
`school`. The backfill migration reused the same "Default School" row
Phase 2 created, rather than creating a second one — verified against
the real development database (all 80 Teachers / 42 Rooms / 10 Subjects
/ 42 StudentGroups / 2100 Lessons preserved, all owned by "Default
School", zero cross-school-resource Lessons found by direct inspection
after migrating).

Two additional, narrowly-scoped safeguards were added ahead of their
originally planned phases, because Phase 3 is what first made them
possible/necessary (see §17, §19, §20 for detail):

- A Lesson-resource cross-school consistency guard
  (`CrossSchoolLessonError`, enforced in `ScheduleService`) — a slice of
  Phase 6, not the full lesson/scheduling access-control system.
- School-scoped `list_teachers()`, threaded through
  `SubstitutionService` and `ScheduleService.staff_schedule()` — a slice
  of Phase 7, not the full Phase 4 authorization system (Phase 4A, below,
  is what added actual current-school resolution).

**Phase 4A (current-school and membership-access foundation) is
implemented** (see §12, §24): `CurrentSchoolService`, session-based
current-school resolution/revalidation/selection, `ChooseSchoolView`,
the no-school-access page, and `SchoolAccessRequiredMixin` replacing
`is_staff`-based gating on every previously `AdministratorRequiredMixin`
-protected view. No database migration was needed — `SchoolMembership`
already had everything Phase 4A required.

**Phase 4B (CRUD school data isolation) is implemented** (see §14):
list-view queryset scoping, Update/Delete IDOR protection, server-side
`school` assignment on Create (removed from the five direct-owner
forms' `Meta.fields`), and `ModelChoiceField` scoping for `PeriodForm`
and `LessonForm`, for all seven CRUD resources (Teacher, Room, Subject,
StudentGroup, AcademicYear, Period, Lesson). No migration was needed.

**Phase 4C (scheduling subsystem school isolation) is implemented**
(see §13–§14): `GeneratePlannedSubstitutionsView`, `StaffScheduleView`,
`TeacherSubstitutionForm`/`TeacherSubstitutionView`, and `ScheduleView`
(for authenticated users with a resolvable current school) are all
scoped. `ScheduleView`'s pre-existing public/anonymous timetable
viewing is deliberately unchanged — see §25. A narrow, defense-in-depth
`SchoolAuthorizationError` guard was added to
`SubstitutionService.generate_planned_substitutions()` only (the one
directly-reachable method that bulk-mutates `Lesson.planned_substitute`);
no other repository or service method was touched, and no migration
was needed.

Phase 4C deliberately stops before the remaining `is_staff` checks in
`schedule.html`/`navigation.py` (they still gate which view *choices*
are shown, e.g. `whole_school`, orthogonal to the data-scoping fixed
here) and before any Django Admin or navigation redesign — that is
Phase 4D.

The next implementation step is:

    Phase 4D: remaining `is_staff` cleanup in templates/navigation,
    full regression/IDOR audit sweep, documentation.

Everything should be implemented incrementally and tested after each
meaningful change.
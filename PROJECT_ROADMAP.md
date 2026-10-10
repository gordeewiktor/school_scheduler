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

## Phase 4B — Plain-CRUD query/object/form scoping (done)

Audit and eliminate unscoped queries such as:

    Model.objects.all()

and:

    Model.objects.get(pk=some_id)

when they can expose another school's data.

- [x] AcademicYear queries scoped by School.
- [x] Teacher queries scoped by School.
- [x] Room queries scoped by School.
- [x] Subject queries scoped by School.
- [x] StudentGroup queries scoped by School.
- [x] Period queries scoped through AcademicYear.
- [x] Lesson queries scoped through AcademicYear/School.

Generic Django views must not allow a principal to manipulate an
object belonging to another school by guessing its primary key.

- [x] Audit and scope UpdateViews' `get_queryset()`.
- [x] Audit and scope DeleteViews' `get_queryset()`.
- [x] Audit CreateViews — force-assign `school` server-side instead of
      exposing it as a client-choosable form field.
- [x] Audit custom `get_object()` calls (none exist beyond Django's
      generic `SingleObjectMixin.get_object()`, which reuses
      `get_queryset()` — confirmed a foreign pk 404s, not 403/200).
- [x] Add tests for cross-school access (404 on another school's id).

ModelChoiceFields must not expose objects belonging to another school.

- [x] AcademicYear choices scoped (`PeriodForm`).
- [x] Teacher/Room/Subject/StudentGroup/Period/planned_substitute
      choices scoped (`LessonForm`).

### Implementation notes

- `SchoolScopedQuerysetMixin` (`views.py`): one `school_filter_lookup`
  attribute + one `get_queryset()` override, applied to
  `SchedulerListView`/`SchedulerUpdateView`/`SchedulerDeleteView`.
  Default lookup `"school"`; `"academic_year__school"` for Period;
  `"start_period__academic_year__school"` for Lesson. This single
  mixin gives Update/Delete their 404-on-foreign-pk protection for
  free, since Django's `SingleObjectMixin.get_object()` is built from
  `get_queryset()`.
- `school` removed from `TeacherForm`/`RoomForm`/`SubjectForm`/
  `StudentGroupForm`/`AcademicYearForm`'s `Meta.fields`.
  `SchedulerCreateView` gained `assign_current_school` (bool, `True` on
  those five Create views) and a `get_form()` override assigning
  `form.instance.school = self.current_school` — in `get_form()`, not
  `form_valid()`, because `ModelForm.validate_unique()` runs during
  `is_valid()`, before `form_valid()`.
- **Bug caught mid-implementation, not after**: removing `school` from
  `Meta.fields` makes Django's own field-exclusion logic drop `school`
  from `validate_unique()` entirely, silently skipping the per-school
  `UniqueConstraint(school, name)` check and letting a duplicate reach
  the database as a raw `IntegrityError`. Fixed with a small
  `_get_validation_exclusions()` override on `BaseStyledModelForm` that
  keeps `school` in the check once the view has set it on the instance.
  `test_create_enforces_per_school_name_uniqueness` caught this the
  first time the new tests were run.
- `BaseStyledModelForm.__init__` accepts a `school=None` kwarg (ignored
  by forms that don't need it); `SchedulerCreateView`/
  `SchedulerUpdateView.get_form_kwargs()` inject it unconditionally.
  `PeriodForm`/`LessonForm` use it to scope their `ModelChoiceField`s
  via `.filter(school=school)` (fail-closed: a missing `school` yields
  zero choices, never every school's).
- Phase 3's `CrossSchoolLessonError` guard is untouched and still
  covered by `tests/integration/test_lesson_school_integrity.py`. It's
  now a defense-in-depth safety net rather than the primary defense for
  the CRUD path — `LessonForm`'s scoped fields mean a foreign id is
  now rejected earlier, as a field-level "select a valid choice" error.

## Phase 4C — Lesson/scheduling subsystem scoping (done)

- [x] Schedule queries scoped by School (`ScheduleView`, for
      authenticated users with a resolvable current school;
      `StaffScheduleView`, always).
- [x] Substitute-teacher queries scoped by School
      (`TeacherSubstitutionForm`).
- [x] `ScheduleView`/`StaffScheduleView`/`TeacherSubstitutionView`/
      `GeneratePlannedSubstitutionsView` validate any user-suppliable
      `academic_year`/resource id against the current school (closes
      the cross-tenant timetable disclosure found during the Phase 4
      inspection).
- [x] A narrow defense-in-depth guard was added at the application-service
      layer for the one directly-reachable, bulk-mutating method
      (`SubstitutionService.generate_planned_substitutions()`) — not a
      blanket `DjangoLessonRepository`/`ScheduleService`/`ConflictService`
      change; those were deliberately left as Phase 3 left them (see
      implementation notes below for why).
- [ ] Lesson queries scoped through AcademicYear/School — not needed:
      inspection found no view/form reachable in Phase 4C that queries
      `Lesson` by an untrusted id outside what `LessonListView`/
      `LessonUpdateView`/`LessonDeleteView` (Phase 4B) already cover.

### Implementation notes

- **`GeneratePlannedSubstitutionsView`** (highest severity — bulk
  mutation): the POSTed `academic_year` id was trusted outright.
  Fixed with `AcademicYear.objects.filter(pk=..., school=self.current_school).exists()`
  before calling the service.
- **`StaffScheduleView`**: `academic_years = AcademicYear.objects.all()` →
  `.filter(school=self.current_school)`. This view had no tests at all
  before Phase 4C; its first tests were written here.
- **`TeacherSubstitutionForm`**: given the same `school=None` fail-closed
  treatment Phase 4B applied to `PeriodForm`/`LessonForm` — it was the
  one CRUD-adjacent form Phase 4B explicitly left alone. Inspection
  also corrected an assumption from the Phase 4C planning prompt: this
  view has no POST/lesson-assignment flow at all, only a read-only
  "who's free" GET lookup — the risk was disclosure, not mutation.
- **`ScheduleView`**: the trickiest one, because it's deliberately
  public. Resolved via `CurrentSchoolService.resolve(request)` called
  directly (not through `SchoolAccessRequiredMixin`, which would force
  login) — scoping `academic_years` and the teacher/room/student_group
  selector only when a current school comes back non-`None`; anonymous
  visitors and authenticated no-membership users keep today's global
  behaviour, confirmed unchanged by the existing `test_public_user_*`
  tests. This is treated as an authentication-boundary decision, not a
  redesign of the (still-undecided) public timetable feature — see
  `PROJECT_CONTEXT.md` §25.
- **Anonymous-safety prerequisite**: `CurrentSchoolService.resolve()`
  had never been called for an unauthenticated user before (every
  existing caller was behind `SchoolAccessRequiredMixin`); doing so
  would have raised `ValueError` filtering `SchoolMembership` by an
  `AnonymousUser`. Fixed first, as its own commit, before touching
  `ScheduleView`.
- **`SchoolAuthorizationError`** (new, `app/domain/exceptions.py`):
  deliberately a sibling of `CrossSchoolLessonError`, not a subclass —
  the two check different things (caller entitlement vs. internal
  lesson consistency) and conflating their names would blur that
  distinction. Added only to
  `SubstitutionService.generate_planned_substitutions()` via an
  optional `school_id` parameter; `generate_plan()` is not reachable
  from any view and was deliberately left unguarded rather than
  extended speculatively.

## Phase 4D — Cleanup and full audit (done)

- [x] Replace remaining `is_staff` checks in `schedule.html` and
      `navigation.py` that gate business features (not Django Admin)
      with current-school/membership checks.
- [x] Full IDOR/security audit sweep against the Phase 4 inspection
      checklist.
- [x] Full regression pass.

### Audit finding fixed in this phase

A pre-implementation audit found one genuine cross-school leak (not
merely a cleanup item): `ScheduleView`'s `whole_school` view gated
access on `request.user.is_staff` alone. An authenticated `is_staff`
user with **zero** `SchoolMembership` rows passed that gate, then hit
the same "no resolvable current school → preserve public/anonymous
behaviour" branch Phase 4C added for genuinely anonymous visitors —
landing on fully unscoped `AcademicYear`/`Teacher`/`Room`/`StudentGroup`
querysets. Reproduced directly before fixing: such an account could
view another school's complete whole-school timetable. Root cause:
`is_staff` (a Django Admin privilege) and "has a current school" (the
application's actual authorization signal) were conflated in exactly
this one place.

### Implementation notes

- **`ScheduleView`**: `current_school` resolved once in `dispatch()`
  (via `CurrentSchoolService.resolve()`) and reused by `_view_choices()`
  and `get_context_data()`, instead of `dispatch()`/`_view_choices()`
  checking `is_staff` while `get_context_data()` separately resolved
  `current_school` — two signals that could (and did) disagree. The
  `whole_school` gate now requires `current_school is not None`.
  Anonymous/public focused-timetable access is untouched by design —
  confirmed unchanged by the existing `test_public_user_*` tests.
- **New `school_context` context processor** (`app/presentation/web/school_access.py`,
  registered in `config/settings.py`): single source of truth for
  `current_school`, `can_manage_school` (`== current_school is not
  None`), and `can_switch_school` (>1 `PRINCIPAL` membership) in every
  template — avoids duplicating `CurrentSchoolService` calls/logic
  between `schedule.html` and `navigation.py`.
- **`schedule.html`**: all 5 `is_staff` checks (Add Lesson, Generate
  Planned Substitutions, 2× clickable lesson-edit-link toggles)
  replaced with `can_manage_school`.
- **`navigation.py`**: `NavigationBuilder.for_request(request)` (was
  `for_user(user)`) shows `SCHOOL_MANAGEMENT_ITEMS` (Timetable, Staff
  Schedule, Lessons, Teacher Substitution) when a current school
  resolves, and appends `Admin` independently based on `is_staff` — the
  *only* remaining `is_staff` check in the whole application (confirmed
  by a final `grep` sweep of `app/`). "Lessons" was previously missing
  from the nav entirely (it has no Django Admin registration, so there
  was no way to reach it from the UI); adding it is what finally fixes
  `test_administrator_navigation`, carried as a "pre-existing failure"
  since Phase 3 — it turned out to be a real defect, not noise.
- **`base.html`**: current-school name shown when `current_school` is
  set; "Switch School" link (to the existing `choose-school` URL — no
  new selection mechanism) shown only when `can_switch_school`. Neither
  shown for anonymous or no-membership users.
- A test-fixture interaction was found and fixed, not a bug: two
  `ChooseSchoolView` rejection tests gave their user exactly one real
  membership, and the new global context processor's `resolve()` call
  (now running on every page, including that error response) legitimately
  auto-selected that single membership per Phase 4A's own established
  behaviour — never the rejected school. Fixed by giving those two
  users a second real membership, so the tests keep proving what they
  always intended (the foreign/nonexistent school is never selected)
  without being incidentally affected by the new global auto-resolution.
- No repository, service, domain, `SchoolMembership`, Django Admin, or
  registration/onboarding changes. No migration needed.

### Final sweep results

- `grep -rn "is_staff" app/` → exactly one remaining hit outside
  comments: `navigation.py`'s `Admin` item — confirmed intentional.
- Broad `.objects.all()`/GET-POST-id sweep → no new unscoped pattern;
  the only two `.objects.all()` hits left are `ScheduleView`'s existing,
  approved anonymous/public fallback branches.
- Full suite: 266 passed, 0 failed — `test_administrator_navigation`
  now passes for the first time since it started failing.

---

# Phase 5 — Periods and Timetable Configuration

An AcademicYear owns its periods.

A principal should eventually be able to configure the school's
timetable structure.

## Periods

- [x] Confirm current Period model is appropriate — unchanged since
      Phase 1/3; no redesign was needed.
- [x] Keep Period associated with AcademicYear (`academic_year`
      ForeignKey, `on_delete=CASCADE`).
- [x] Ensure period order is unique within AcademicYear
      (`UniqueConstraint(academic_year, order)`).
- [x] Ensure period names are unique within AcademicYear
      (`UniqueConstraint(academic_year, name)`).
- [x] Preserve start/end-time validation (`Period.clean()` delegates to
      the domain `Period`, raising `InvalidPeriodError` on an invalid
      range).
- [x] Support LESSON periods (`Period.Kind.LESSON`).
- [x] Support BREAK periods (`Period.Kind.BREAK`).

  These were already true going into Phase 5 (Phase 1/3 groundwork);
  this checklist was simply never flipped at the time.

## Timetable configuration

- [x] Number of periods per day.
- [x] Period names (auto-generated as "Period N"/"Break after Period N"
      by the generator below; still individually renameable afterward
      via the existing legacy Period CRUD).
- [x] Period order.
- [x] Start times.
- [x] End times.
- [x] Breaks.
- [x] Default lesson duration.

  Implemented via a one-shot **period generation workflow**
  (`b7a3335`), not a per-field configuration system — avoids the
  redundant-configuration trap this section originally warned about.
  `PeriodGenerationService` (`app/application/services/period_generation.py`)
  takes a lesson count, first start time, lesson duration, and an
  optional list of `BreakAfter(after_period, duration_minutes)`
  entries, and derives every period's name/order/start/end time by
  walking forward from the first start time — validated to stay within
  a single day. It only ever runs once per AcademicYear
  (`PeriodsAlreadyExistError` if periods already exist — this is a
  bulk-create tool, not an editor) and is school-authorization-checked
  (`SchoolAuthorizationError` if the academic year isn't the caller's
  school's). Reachable via `PeriodGenerationView`
  (`/legacy/periods/generate/`) and `GeneratePeriodsForm`. Individual
  periods remain editable/deletable afterward through the pre-existing
  legacy Period CRUD views — this workflow only replaces *initial*
  setup, not ongoing editing.

---

# Phase 6 — Lessons and Scheduling

## Lessons

- [x] Ensure lessons are accessible only within the current school.
      Established by Phase 4B/4C (`SchoolScopedQuerysetMixin` on
      `LessonListView`/`LessonUpdateView`/`LessonDeleteView`;
      `LessonForm` scoped to `school=self.current_school` for
      Create/Update) and confirmed by the Phase 6 audit — this
      checkbox was simply never flipped at the time.
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
  cross-school Lesson possible. Phase 6 closed the two remaining gaps
  the Phase 6 audit found: the Lesson form's dropdowns (already scoped
  since Phase 4B) and `planned_substitute` are now both covered —
  `_ensure_same_school()` includes `planned_substitute_id`'s school in
  the same invariant it already applied to teacher/room/subject/
  student group/period.

## Scheduling

- [x] Audit ScheduleService — found `create_lesson`/`update_lesson` had
      no caller-supplied `school_id` check, unlike
      `SubstitutionService.generate_planned_substitutions`. Closed by
      adding an optional `school_id` parameter to both, raising the
      existing `SchoolAuthorizationError` on mismatch (mirroring the
      Phase 4C precedent); wired from `LessonWriteMixin.form_valid()`.
      `school_id` remains optional, not mandatory.
- [x] Audit ConflictService — no gap found. `list_potential_conflicts()`
      scopes candidates by `academic_year_id`, itself always derived
      from an already-same-school-validated Period, so cross-school
      conflict mixing is structurally impossible. Left unchanged.
- [x] Audit LessonRepository — no gap found. Repository methods
      correctly take raw ids with no school awareness by design;
      authorization belongs in the service/view layers above it, which
      now enforce it. Left unchanged (only the additive
      `planned_substitute_id` parameter/field described above).
- [x] Ensure all scheduling operations operate within one school.
- [x] Confirm conflict detection cannot mix school data.
- [x] Add multi-school service tests — service-level tests for the new
      `school_id` guard and the `planned_substitute` invariant in
      `tests/application/test_schedule_service.py` and
      `tests/integration/test_lesson_school_integrity.py`, plus a
      `LessonUpdateView` cross-school-resource-swap regression test in
      `tests/integration/test_crud_school_isolation.py`.

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

- [x] Confirm existing login flow — Django's built-in
      `auth_views.LoginView`/`LogoutView` (`config/urls.py`), unchanged;
      no custom login view was needed.
- [x] Connect authenticated User to Principal/School — already done in
      Phase 4A via `SchoolMembership`/`CurrentSchoolService`.
- [x] Define behavior for users without a school — already done in
      Phase 4A (`SchoolAccessRequiredMixin`'s "no school access" page);
      Phase 8 added the complementary way *out* of that state
      (self-service registration, below).

## Registration

- [x] Create registration flow — `RegistrationView`
      (`/accounts/register/`, `app/presentation/web/views.py`),
      deliberately not behind `SchoolAccessRequiredMixin` since this is
      how a user gets their *first* `SchoolMembership`.
- [x] Allow a new user to create a School.
- [x] Create the Principal/membership relationship.
- [x] Perform account + school creation in one transaction —
      `register_principal()` (`app/application/services/registration.py`)
      wraps `User.objects.create_user()` + `School.objects.create()` +
      `SchoolMembership.objects.create()` in one `transaction.atomic()`
      block, validating the password with Django's configured
      validators before anything is persisted.
- [x] Prevent accidental creation of orphaned school/user records — the
      same `transaction.atomic()` block; `RegistrationView.form_valid()`
      also catches the realistic username-taken race (`IntegrityError`)
      and confirms the School it would have orphaned was rolled back.

  Implemented in `22d3225`, with service/form/view tests
  (`tests/application/test_registration.py`,
  `tests/presentation/test_registration_form.py`,
  `tests/integration/test_registration_view.py`).
  `load_demo_data`'s two demo principals (Phase 9) are created through
  this same `register_principal()` call, not a separate path.

## Authorization

- [x] Replace inappropriate reliance on `is_staff` for school
      ownership — already done in Phase 4 (only remaining `is_staff`
      check is the Django Admin nav item).
- [x] Ensure principals can only manage their own school — already done
      in Phase 4B/4C/4D.
- [ ] Decide whether different school roles are needed — still open;
      `SchoolMembership.role` only ever has `PRINCIPAL`. Tracked under
      Open Decisions below.
- [x] Add authorization tests — extensive coverage already exists from
      Phase 4; Phase 8 added its own registration-specific tests
      (listed above).

---

# Phase 9 — Demo Data

- [x] Update `load_demo_data`.
- [x] Remove assumptions about one global AcademicYear.
- [x] Create a demo School.
- [x] Create a demo Principal/user if appropriate.
- [x] Create school-specific teachers.
- [x] Create school-specific rooms.
- [x] Create school-specific subjects.
- [x] Create school-specific student groups.
- [x] Create AcademicYear for the demo school.
- [x] Create periods and lessons.
- [x] Verify substitute-teacher generation.

  Implemented in `b4aa397`: `load_demo_data` now loads **two**
  independent demo schools (Riverside High, Lincoln Academy) with
  deliberately identical academic-year/subject/teacher/room/
  student-group names, specifically to demonstrate that same-named
  records stay fully isolated once they belong to different Schools.
  Each demo principal (`principal_riverside`/`principal_lincoln`, both
  `Demo-Pass-2026!`) is created through the same `register_principal()`
  call the web registration flow uses (Phase 8), not a separate path.
  The command is idempotent: re-running it reuses each demo principal's
  existing School (looked up via their own `SchoolMembership`) rather
  than creating a second one. Verified via
  `tests/integration/test_load_demo_data_command.py`.

  A pre-multi-school leftover school ("Default School", with generic
  "Teacher 01"… names and 2100 lessons, created by the single-school
  version of this command and never cleaned up) was identified and
  deleted directly against the real dev database during the 2026-10-08
  polish session below — it predated this rewrite and was never one of
  the two demo schools.

---

# Phase 10 — Testing & Quality Audit

Done. Split into two sessions: a read-only audit (no code changes) that
inspected every test file against this checklist and produced a
findings report, followed by an implementation session that fixed the
one confirmed defect the audit found and closed the real coverage
gaps. See the Session Log below for both.

## Unit/domain tests

- [x] Period validation (`tests/domain/test_timeslot_validation.py`,
      `tests/infrastructure/test_period_constraints.py`).
- [x] Domain scheduling rules (`tests/domain/test_lesson.py`).
- [x] Conflict rules (`tests/application/test_conflict_service.py`
      fake-repository unit tests, plus
      `tests/infrastructure/test_django_lesson_conflicts.py` against
      the real DB).
- [x] Substitute-teacher rules
      (`tests/application/test_substitution_service.py` — fairness,
      tie-breaking, fallback, school exclusion).

## Application tests

- [x] ScheduleService (`tests/application/test_schedule_service.py`).
- [x] ConflictService (`tests/application/test_conflict_service.py`).
- [x] SubstitutionService
      (`tests/application/test_substitution_service.py`).
- [x] Multi-school isolation — the single most thoroughly tested
      concern in the whole suite; see the Integration/web row below.

## Infrastructure tests

- [x] Repository filtering
      (`tests/integration/test_django_lesson_repository.py`).
- [x] Teacher queries
      (`tests/infrastructure/test_django_lesson_conflicts.py::test_list_teachers_excludes_teachers_from_another_school`).
- [x] Lesson queries (`tests/integration/test_django_lesson_repository.py`).
- [x] AcademicYear queries (`tests/infrastructure/test_academic_year_school.py`).
- [x] School-specific data access — covered throughout the
      infrastructure and integration suites.

## Integration/web tests

- [x] Login — was a genuine gap (every other test authenticated via
      `force_login()` or registration's auto-login; the real
      `POST /accounts/login/` flow had zero direct coverage). Closed in
      the implementation session: successful login, failed login
      (wrong password), logout, and immediate access denial right
      after logout (`tests/integration/test_web_pages.py`).
- [x] Principal access (`tests/integration/test_current_school_access.py`).
- [x] AcademicYear / Teacher / Room / Subject / StudentGroup access
      (`tests/integration/test_crud_school_isolation.py`, parametrized
      across all five).
- [x] Lesson access (`tests/integration/test_crud_school_isolation.py`,
      `tests/integration/test_web_pages.py`).
- [x] Schedule access (`tests/integration/test_scheduling_school_isolation.py`).
- [x] Substitute access — the dedicated "Teacher Substitution" page
      was removed in the 2026-10-08 polish pass, but the underlying
      access paths (`GeneratePlannedSubstitutionsView`, staff schedule,
      `SubstitutionService.available_teachers()`) remain tested.
- [x] Cross-school access attempts return 403/404 and never expose
      data — verified both by status code and by asserting the
      response *body* never contains the other school's data
      (`test_is_staff_without_membership_cannot_use_whole_school_view`
      and others reproduce the one real historical vulnerability found
      in Phase 4D as a standing regression test).

## Regression

- [x] Run complete test suite — 339 passed, 0 failed.
- [x] Fix broken fixtures — none were found broken; not applicable.
- [x] Verify existing functionality still works —
      `manage.py check` and `makemigrations --check --dry-run` both
      clean.
- [x] Test with at least two schools containing overlapping names/data
      — `tests/integration/test_load_demo_data_command.py`'s
      `test_load_demo_data_reuses_identical_names_across_independent_schools`
      and `test_load_demo_data_never_mixes_lessons_across_the_two_schools`,
      plus dozens of two-school isolation tests throughout.

### Confirmed defect found and fixed

`ProtectedDeleteMixin` correctly blocked deleting a Teacher/Room/
Subject/StudentGroup/Period/AcademicYear still referenced by a Lesson,
but the user never saw why: `object_confirm_delete.html` never
rendered `form.non_field_errors`. Reproduced empirically (a throwaway,
non-persisted test confirmed the exact symptom) before fixing. Fix:
three lines in the template. Also found, via direct MRO tracing of
Django's `BaseDeleteView`, that `ProtectedDeleteMixin.post()`'s own
`except ProtectedError` handler was unreachable dead code — `post()`
calls `self.form_valid()`, which dispatches to this mixin's
`form_valid()` override first, so the exception is always caught there
and never reaches `post()`'s own try/except. Removed the dead handler.
Regression test: `tests/integration/test_protected_delete.py`,
parametrized across all six affected resource types, plus one
unrelated-resource-still-deletes-normally guard test.

### Coverage gaps closed this session

- Login/logout (`test_login_with_valid_credentials_redirects_to_schedule`,
  `test_login_with_incorrect_password_shows_error_and_does_not_authenticate`,
  `test_logout_redirects_to_login_and_ends_session`,
  `test_protected_page_is_denied_immediately_after_logout`).
- Lesson create/update/delete redirect destinations, previously only
  checked for `302` without checking *where* — relevant because the
  2026-10-08 polish pass changed these from the removed `lesson-list`
  page to `schedule`, and nothing had verified the new destination.
- Open-redirect protection (`_safe_next_url()`) — previously only the
  "accept a safe `next`" path was exercised implicitly; the "reject an
  unsafe `next`" path had no test at all. Verified these tests are
  meaningful by temporarily removing the check and confirming they
  fail, then restoring it.
- `LessonWriteMixin.form_valid()`'s `except (CrossSchoolLessonError,
  SchoolAuthorizationError)` branch — structurally unreachable through
  a real form submission (`LessonForm`'s querysets are already scoped
  to the current school), so tested with a narrowly-scoped
  `monkeypatch` of the service factory rather than left uncovered.

### Audit recommendations deliberately left unimplemented

- `GeneratePlannedSubstitutionsView`'s defense-in-depth
  `SchoolAuthorizationError` catch — the audit flagged it as untested,
  but it's a backstop behind a view-layer check that's already tested,
  and the service-level guard it wraps is already covered in
  `tests/application/test_substitution_service.py`. Adding a test here
  would be effort disproportionate to risk; left as-is.
- Django Admin row-level school scoping — explicitly out of scope for
  Phase 10 (a separate architectural decision; see §24 of
  `PROJECT_CONTEXT.md`).
- Production-readiness settings (`DEBUG`, `SECRET_KEY`,
  `ALLOWED_HOSTS`) — explicitly Phase 11, untouched.

---

# Phase 11 — Production Preparation

Phase 11 is in progress, not complete. A read-only audit ran first
(settings/security/deployment-readiness inspection, no changes), then
the database was migrated to PostgreSQL, then settings were made
environment-driven and production security/logging/static-file
configuration was added. **Deployment infrastructure itself (hosting,
WSGI server, static-file serving, a real domain) remains entirely
undone — see the checklist below.**

Before deployment:

- [x] Review production Django settings — audited, then acted on (see
      Session Log).
- [x] Move secrets to environment variables — `SECRET_KEY` now has
      **no production fallback** (`ImproperlyConfigured` if unset when
      `DJANGO_ENV=production`); database credentials were already
      env-driven from the PostgreSQL migration.
- [x] Configure `DEBUG=False` — now the production default
      (`DJANGO_ENV=production`), individually overridable, parsed via
      a safe boolean parser (`config/env.parse_bool`) rather than
      `bool(os.environ.get(...))`.
- [x] Configure allowed hosts — required with no default when
      `DJANGO_ENV=production`; comma-separated parsing trims whitespace
      and drops empty entries.
- [x] Configure CSRF/trusted origins appropriately — `CSRF_TRUSTED_ORIGINS`
      is environment-driven with no invented placeholder domain; empty
      by default since it's only needed once a real HTTPS domain
      exists.
- [x] Configure production database — PostgreSQL is the project's
      standard backend for dev, test, and production alike, replacing
      SQLite entirely (see the 2026-10-10 Session Log entries).
- [x] Configure static files — `STATIC_ROOT` set;
      `collectstatic --noinput` verified to succeed (127 files, all
      Django Admin's own CSS/JS — this application has none of its
      own). Serving the collected files over HTTP still needs a
      decision once a host is chosen — documented in `README.md`, not
      yet implemented.
- [ ] Configure media files if required — not applicable; this
      application has no file-upload features.
- [x] Configure logging — a minimal, always-on `LOGGING` config now
      routes Django/application errors to stderr regardless of
      `DEBUG`, matching a containerized/platform deployment's expected
      log capture. No file handling, no email, no new dependency.
- [~] Configure error handling — Django's own default production
      error pages (plain, no information disclosure) now apply
      correctly since `DEBUG=False` is wired up in production; no
      custom branded 404/500 templates were added (not requested, low
      value before a deployment target exists).
- [x] Review authentication/security settings — audited, then fixed:
      `DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS`, HTTPS redirect, secure
      cookies, and conservative HSTS are all now environment-driven.
      Verified via a simulated-production `check --deploy` run: only
      `security.W005`/`W021` (HSTS subdomains/preload) remain, both
      deliberately not enabled by default per explicit instruction.
- [x] Review school data isolation — re-verified intact, twice now
      (after the PostgreSQL migration, and again after this session's
      settings changes): full test suite passing, existing
      authorization/isolation tests unmodified.
- [x] Review database backups — a `pg_dump`/`psql`-restore workflow is
      documented in `README.md`; a verified SQLite backup exists at
      `backups/db.sqlite3.pre-postgres-backup-20261010` (gitignored,
      rollback reference only).

### Orphaned superuser (investigated, not resolved)

The local development database carries a superuser account,
`principal` (id 1, `is_staff=True`, `is_superuser=True`, no
`SchoolMembership`), unrelated to the two demo principals. See
`PROJECT_CONTEXT.md` §24 for the full investigation (how it was
created, why it isn't necessary, and why it's safe as long as
production is never seeded from a dump of the local dev database).
**Not deleted, modified, or had its password reset** — per explicit
instruction, this remains a recommendation (clean it up locally
whenever convenient) and a documentation item (README's production
section now warns against seeding prod from a dev dump), not a code
change.

### Still open before an actual deployment

- No hosting provider chosen (explicitly deferred to Phase 12).
- No WSGI server (e.g. gunicorn) added — `config.wsgi.application`
  exists but nothing production-grade serves it yet.
- No static-file-serving solution chosen (whitenoise, nginx, or the
  host's own handling) — `collectstatic` succeeds, but nothing serves
  `STATIC_ROOT` over HTTP yet.
- No real production domain, so `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS`
  can't be filled with real values yet — only verified with
  placeholders.
- `SECURE_HSTS_INCLUDE_SUBDOMAINS`/`SECURE_HSTS_PRELOAD` intentionally
  still `False` — a deliberate choice, not a gap, per explicit
  instruction not to enable either by default.

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

Phase 11: prepare for production. Audited settings/security/
deployment-readiness first (read-only), then — per explicit decision —
implemented and verified PostgreSQL as the standard database backend
for dev, test, and production.

## Current status

Phases 1–10 are complete. Phase 11 is **in progress, not complete**:
the database is now PostgreSQL everywhere (verified — see the Phase 11
section and 2026-10-10 Session Log entry), but `DEBUG`, `SECRET_KEY`,
`ALLOWED_HOSTS`, HTTPS/cookie security, static files, and logging are
all still exactly as the audit found them — this application remains
not production-ready. 339 tests pass against PostgreSQL;
`manage.py check`, `makemigrations --check --dry-run`, and
`migrate --check` are all clean.

Deferred, still out of scope: Django Admin row-level scoping, any
`SchoolMembership` role beyond `PRINCIPAL`.

## Immediate next step

Finish Phase 11: env-driven `DEBUG`/`SECRET_KEY`/`ALLOWED_HOSTS`,
HTTPS/cookie settings, `STATIC_ROOT` + static serving, and minimal
`LOGGING` — all identified by the audit, none implemented yet.

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
- [x] Final registration/user onboarding flow — resolved by Phase 8:
      self-service registration (`register_principal()`,
      `RegistrationView`); no invitation/multi-user-per-school flow
      exists yet, but none was planned for this phase.
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

Phase 4A was implemented and verified, and has since been committed
(`b538cc1`).

### Next

Move to Phase 4B (plain-CRUD query/object/form scoping).

## 2026-09-20 — Phase 4B: CRUD school data isolation

### Completed

- `SchoolScopedQuerysetMixin` (`views.py`): `school_filter_lookup`
  class attribute (default `"school"`) + `get_queryset()` override,
  applied to `SchedulerListView`, `SchedulerUpdateView`, and
  `SchedulerDeleteView`. `PeriodListView`/`PeriodUpdateView`/
  `PeriodDeleteView` override the lookup to `"academic_year__school"`;
  `LessonListView`/`LessonUpdateView`/`LessonDeleteView` override it to
  `"start_period__academic_year__school"`. This scopes every list page
  to the current school and, since Django's
  `SingleObjectMixin.get_object()` is built from `get_queryset()`,
  makes Update/Delete 404 on another school's id for free — verified
  directly (GET and POST) rather than assumed.
- `SchedulerCreateView` gained `assign_current_school` (bool flag, `True`
  on `TeacherCreateView`/`RoomCreateView`/`SubjectCreateView`/
  `StudentGroupCreateView`/`AcademicYearCreateView` only) and a
  `get_form()` override assigning `form.instance.school =
  self.current_school` — before `form.is_valid()` runs, not after, so
  the per-school `UniqueConstraint(school, name)` check validates
  against the real school.
- Removed `"school"` from `TeacherForm`/`RoomForm`/`SubjectForm`/
  `StudentGroupForm`/`AcademicYearForm`'s `Meta.fields` — it is never a
  client-choosable field for these five models.
- **Caught and fixed a real Django subtlety during implementation**
  (not discovered later): removing `school` from `Meta.fields` makes
  Django's `ModelForm._get_validation_exclusions()` exclude it from
  `validate_unique()` entirely, silently skipping the per-school
  uniqueness check and letting a duplicate name reach the database as
  a raw `IntegrityError`. Fixed with a targeted
  `_get_validation_exclusions()` override on `BaseStyledModelForm`:
  keep `school` in the check once the view has actually set it on the
  instance. `test_create_enforces_per_school_name_uniqueness` failed
  with exactly this `IntegrityError` on the first run, before the fix.
- `BaseStyledModelForm.__init__` accepts a `school=None` keyword
  (silently ignored by forms that don't need it).
  `SchedulerCreateView`/`SchedulerUpdateView.get_form_kwargs()` both
  inject `school=self.current_school` unconditionally. `PeriodForm`
  uses it to scope `academic_year` to
  `AcademicYear.objects.filter(school=school)`; `LessonForm` uses it to
  scope `teacher`, `planned_substitute`, `subject`, `room`,
  `student_group` (all `.filter(school=school)`) and `start_period`
  (`.filter(academic_year__school=school)`). Every one fails *closed*
  (zero choices) rather than falling back to `.objects.all()` if
  `school` is ever missing.
- Verified Phase 3's `CrossSchoolLessonError` guard
  (`ScheduleService._ensure_same_school`) is unmodified and its test
  file (`tests/integration/test_lesson_school_integrity.py`) still
  passes unchanged — it's now a defense-in-depth safety net rather than
  the primary defense for the CRUD path, since `LessonForm`'s scoped
  fields reject a foreign id earlier, as a field-level error.
- Added `make_principal_client` to `tests/conftest.py` — a factory
  fixture (built on the existing `make_user`/`make_school`/
  `make_membership`) returning a logged-in `Client` for a fresh
  School's principal, with the School attached as `.school` for reuse
  in test bodies.
- Added `tests/integration/test_crud_school_isolation.py` (61 tests):
  list-only-shows-current-school, GET/POST Update and Delete
  404-on-foreign-pk (with object-unchanged/object-remains assertions),
  and Create-assigns-current-school/no-school-field/
  per-school-uniqueness/cross-school-name-reuse, parametrized across
  Teacher/Room/Subject/StudentGroup/AcademicYear; dedicated Period
  tests (list/update/delete IDOR, `academic_year` form scoping,
  reject-foreign-academic-year on both create and update); dedicated
  Lesson tests (list/update/delete IDOR, form-only-offers-current-school
  for every field, reject-foreign-id parametrized across
  teacher/planned_substitute/subject/room/student_group, and a
  dedicated `start_period` case).
- Fixed `tests/integration/test_web_pages.py`'s fixtures: `lesson_form_data`
  now depends on `authenticated_client` and reuses `authenticated_client.school`
  (exposed as a `.school` attribute on the fixture's `Client`) instead of
  creating its own unrelated school — the two fixtures previously
  referred to different schools, which only mattered once forms/querysets
  became school-scoped.
- Updated 5 tests whose premise Phase 4B's scoping directly affected:
  `test_create_period_from_time_input`/`test_invalid_period_time_returns_form_errors`
  (reuse `authenticated_client.school` instead of an unrelated local
  school), `test_academic_year_list_shows_school_column` (same, plus
  asserting the real school name), and a rewrite of
  `test_create_academic_year_requires_a_school`/
  `test_create_academic_year_with_school_succeeds` into
  `test_create_academic_year_has_no_school_field`/
  `test_create_academic_year_assigns_current_school` — their old premise
  (the client selects a school) is exactly what Phase 4B removes.
  `test_lesson_form_rejects_room_from_another_school`'s assertion moved
  from `form.non_field_errors()` (Phase 3's guard) to
  `form.errors["room"]` (Phase 4B's field-level rejection) — the
  behavior it protects is unchanged, only which layer catches it.
- Verification performed:
  - `manage.py check` → no issues.
  - `makemigrations --check --dry-run` → no changes detected (no
    schema change was needed).
  - Full pytest suite → 236 passed, 1 pre-existing failure unrelated to
    this change (`test_administrator_navigation`, same failure present
    before Phase 4B).
  - `git diff` reviewed in full: changes limited to
    `app/presentation/web/views.py`, `app/presentation/web/forms.py`,
    `tests/conftest.py`, `tests/integration/test_web_pages.py`, plus
    the new isolation test file — `ScheduleView`, `StaffScheduleView`,
    `TeacherSubstitutionView`/`TeacherSubstitutionForm`,
    `GeneratePlannedSubstitutionsView`, `DjangoLessonRepository`,
    `ScheduleService`, `SubstitutionService`, `ConflictService`, and
    `SchoolMembership` are all untouched.
- Explicitly NOT done (deferred to 4C/4D, per scope): `ScheduleView`/
  `StaffScheduleView`/`TeacherSubstitutionView`/
  `GeneratePlannedSubstitutionsView` remain fully unscoped; no deeper
  repository/service school guard beyond Phase 3's was added; no
  template/navigation `is_staff` cleanup; no URL redesign; no `school`
  FK added to `Lesson`; no `SchoolMembership` changes; no registration/
  invitation/onboarding/billing/deployment work.

### Current task

Phase 4B was implemented and verified, and has since been committed
(`e030c25`).

### Next

Move to Phase 4C (Lesson/scheduling subsystem scoping).

## 2026-09-21 — Phase 4C: Scheduling subsystem school isolation

### Completed

Implemented in the approved order, one commit per logical step, running
the relevant tests plus a full regression pass after each:

- **4C-1** (`b77df94`) — `CurrentSchoolService.resolve()` now returns
  `None` immediately for an unauthenticated user, instead of raising
  `ValueError` when filtering `SchoolMembership` by an `AnonymousUser`.
  Prerequisite for 4C-2 (`ScheduleView` is the first caller that can be
  anonymous).
- **4C-5** (`0ced268`) — `GeneratePlannedSubstitutionsView` now
  validates the POSTed `academic_year` id belongs to
  `self.current_school` before calling the service. Previously any
  authenticated principal could trigger a bulk `planned_substitute`
  mutation on another school's lessons — the highest-severity finding
  from the Phase 4C inspection. Done first (out of dependency order)
  because it was the highest-severity, fully independent fix.
- **4C-3** (`984b6a9`) — `StaffScheduleView`'s `academic_years` scoped
  to `self.current_school`. This view had no tests before Phase 4C;
  wrote its first ones here.
- **4C-4** (`a482d8d`) — `TeacherSubstitutionForm` gained the same
  `school=None` fail-closed treatment Phase 4B gave `PeriodForm`/
  `LessonForm`; `TeacherSubstitutionView` passes `school=self.current_school`.
  Inspection corrected an assumption going in: this view has no POST/
  lesson-assignment flow, only a read-only "available teachers" GET
  lookup — the risk was disclosure, not mutation.
- **4C-2** (`4ee3e7e`) — `ScheduleView`'s `academic_years` and the
  teacher/room/student_group selector scoped, but only when
  `CurrentSchoolService.resolve(request)` returns a school (called
  directly, not via `SchoolAccessRequiredMixin`, which would force
  login and break the public path). Anonymous visitors and
  authenticated users with no resolvable current school keep exactly
  today's global behaviour — confirmed by the existing
  `test_public_user_can_access_focused_schedule`/
  `test_public_user_can_access_student_group_and_room_schedules`/
  `test_public_user_cannot_access_whole_school_schedule` passing
  unchanged. Also fixed 3 existing tests
  (`test_schedule_uses_period_columns_and_breaks`,
  `test_schedule_defaults_to_latest_academic_year`,
  `test_teacher_view_only_exposes_teacher_selector`) that created an
  ad-hoc School unrelated to `authenticated_client.school` — the same
  fixture pattern Phase 4B had to fix for the CRUD views.
- **4C-6** (`3fba043`) — added `SchoolAuthorizationError`
  (`app/domain/exceptions.py`), a sibling of `CrossSchoolLessonError`
  rather than a subclass (different concern: caller entitlement vs.
  internal lesson consistency). Added an optional `school_id`
  parameter to `SubstitutionService.generate_planned_substitutions()`
  only — the one method reachable from a view that bulk-mutates
  `Lesson.planned_substitute` — validated against
  `get_academic_year_school_id()` (already existed from Phase 3).
  `generate_plan()` is not reachable from any view and was deliberately
  left unguarded. `GeneratePlannedSubstitutionsView` now passes
  `school_id=self.current_school.id` and treats
  `SchoolAuthorizationError` as a safety net, not the primary check
  (4C-5's view-layer check already prevents it from firing in normal
  operation).
- **4C-7** — regression/cleanup, folded into each step above rather
  than saved for the end, plus a final full-suite pass.

No changes to `DjangoLessonRepository`, `app/application/ports/repositories.py`,
`ScheduleService`, `ConflictService`, `SchoolMembership`, URLs,
templates, navigation, or Django Admin — confirmed via
`git diff --stat e030c25..HEAD` after every commit.

New test file `tests/integration/test_scheduling_school_isolation.py`
(19 tests) covers: same-school access works, cross-school read is
blocked (empty/degraded state, never the other school's data),
cross-school mutation is blocked (verified via a fresh DB query, not
the response), and foreign/nonexistent ids fail closed, for all four
views/forms. `tests/application/test_substitution_service.py` gained 3
tests for the new service-level guard (rejects mismatch, accepts
match, skips the check when `school_id` is omitted).

Verification performed after the final commit:
- `manage.py check` → no issues.
- `makemigrations --check --dry-run` → no changes detected (no schema
  change was needed).
- Full pytest suite → 254 passed, 1 pre-existing failure unrelated to
  this change (`test_administrator_navigation`, same failure present
  before Phase 4C).
- `git diff --stat e030c25..HEAD` reviewed: 8 files changed, all within
  the approved scope.

### Current task

Phase 4C is implemented, verified, and committed.

### Next

Move to Phase 4D (remaining `is_staff` cleanup in templates/navigation,
full regression/IDOR audit sweep, documentation).

## 2026-09-19 — Phase 4D: Cleanup and full authorization audit

### Completed

Preceded by an inspection-only session that produced a full findings
report before any code changed; implemented in the approved order, one
logical step at a time, running tests after each:

- **4D-1** — Fixed the `ScheduleView` `whole_school` vulnerability found
  during the audit (see the Phase 4D section above for detail):
  `current_school` resolved once in `dispatch()`, reused by
  `_view_choices()`/`get_context_data()`; the gate now requires
  `current_school is not None` instead of `is_staff`. 3 tests added
  (non-staff principal can use it; scoped correctly; is_staff-without-
  membership denied — the last one reproducing the vulnerability and
  proving it's closed).
- **4D-2** — Added the `school_context` context processor
  (`current_school`, `can_manage_school`, `can_switch_school`),
  registered in `config/settings.py`, as the single reusable source of
  truth for templates. Found and fixed a real (non-security) test
  interaction: two `ChooseSchoolView` rejection tests had only one real
  membership each, so the processor's `resolve()` call — now running on
  every page — legitimately auto-selected it per Phase 4A's existing
  behaviour; gave both users a second membership so the tests keep
  testing what they intended.
- **4D-3** — Replaced all 5 `is_staff` checks in `schedule.html` with
  `can_manage_school`. Added tests proving a non-staff principal both
  *sees* and can *use* Add Lesson/Generate Planned Substitutions
  end-to-end, and that is_staff-without-membership sees neither.
- **4D-4** — Rewrote `navigation.py`: `SCHOOL_MANAGEMENT_ITEMS`
  (Timetable, Staff Schedule, Lessons, Teacher Substitution) shown when
  a current school resolves; `Admin` appended independently based on
  `is_staff`.
- **4D-5** — Fixed `test_administrator_navigation` (real defect: no
  "Lessons" link existed at all, and "Teacher Substitution" is now
  correctly included per the approved decision) rather than weakening
  it, and added `test_non_staff_principal_navigation`,
  `test_is_staff_without_membership_navigation`, and
  `test_anonymous_navigation` alongside the existing
  `test_regular_user_navigation`. Full suite went from 1 failure to 0
  for the first time since this failure was first noted in Phase 3.
- **4D-6** — Added the current-school indicator and "Switch School"
  link to `base.html`, driven by `current_school`/`can_switch_school`
  from the same context processor; links to the existing
  `choose-school` URL, no new selection mechanism. 4 tests: multi-school
  user sees both; single-school user sees neither the switch link;
  no-membership and anonymous users see neither the indicator nor the
  link.
- **4D-7** — Final sweep: `grep -rn "is_staff" app/` → exactly one
  remaining hit, `navigation.py`'s `Admin` item, confirmed intentional;
  no other `is_staff`/`is_superuser` check exists anywhere in the
  templates or Python code. Broad `.objects.all()`/GET-POST-id sweep →
  no new unscoped pattern; the only two `.objects.all()` hits left are
  `ScheduleView`'s existing, approved anonymous/public fallback
  branches (`_academic_years`, `_selector`).
- **4D-8** — Final verification (below) and this documentation update.
  Per explicit instruction, **nothing has been committed**.

Verification performed:
- `manage.py check` → no issues.
- `makemigrations --check --dry-run` → no changes detected (no schema
  change was needed).
- Full pytest suite → **266 passed, 0 failed** — the `test_administrator_navigation`
  failure carried since Phase 3 is genuinely resolved, not just
  reconfirmed as unrelated.
- `git diff --stat` reviewed: 9 files changed
  (`navigation.py`, `school_access.py`, `base.html`, `schedule.html`,
  `views.py`, `config/settings.py`, and 3 test files) — all within the
  approved scope. No repository, service, domain, `SchoolMembership`,
  Django Admin, or registration/onboarding file touched.

### Current task

Phase 4D is implemented and verified. Working tree is intentionally
**uncommitted**, per this session's explicit instruction, pending
review.

### Next

Review the diff, commit when ready, then decide what comes after
Phase 4 (Django Admin scoping and registration/onboarding are the two
explicitly-deferred candidates, but neither has been scoped as its own
phase yet).

## 2026-09-19 (continued) — Phases 5, 6, 8, 9: retroactively documented

The Phase 4D diff above was committed (`ae0e7ad`), and three more
phases were implemented and committed the same day, but this document
was never updated for any of them at the time — their checkboxes sat
unchecked for weeks while the actual code moved on. This entry
backfills that record from the commit history rather than rewriting
history as if it had been tracked live; see the Phase 5/8/9 sections
above for the checklist detail.

- `b7a3335` **Add period generation workflow** — Phase 5. A
  `PeriodGenerationService` that bulk-creates a school's first period
  schedule from a lesson count, start time, duration, and breaks,
  rather than a general per-field timetable-configuration system.
- `05dde95` **Harden lesson school isolation** — the Phase 6 audit
  (this is the one commit that *did* update this document at the
  time — see the Phase 6 section above for its own detail).
- `22d3225` **Add principal registration flow** — Phase 8. Self-service
  registration (`register_principal()`, atomic User+School+
  SchoolMembership creation, `RegistrationView`); Django's existing
  built-in login view needed no changes.
- `b4aa397` **Add multi-school demo data** — Phase 9. Rewrote
  `load_demo_data` to seed two independent, identically-structured
  demo schools instead of one, specifically to exercise isolation.

### Current task

Phases 1–9 are implemented, verified, and committed (confirmed via a
fresh `manage.py check` / `makemigrations --check --dry-run` / full
pytest run during this doc-sync session, not just by reading the old
commits). Phase 10/11/13 remain unscoped.

### Next

Pick one of Phase 10 (testing audit), Phase 11 (production prep), or
Phase 13 (portfolio polish) as the next real slice of work.

## 2026-10-08 — Polish pass: demo readiness

Not a roadmap phase — a focused cleanup pass preparing the app to be
shown to someone else, prompted by manually attaching the old
"principal" user to "Default School" via `create_school` and then
looking at the live site end to end.

### Completed

- Removed the duplicate navigation link: the "School Scheduler" brand
  and the "Timetable" nav item both pointed at `schedule`. Kept
  **Timetable** (every existing navigation test already treated it as
  the canonical link across anonymous/regular/principal/admin states)
  and changed the brand in `base.html` from an `<a>` to a plain
  `<span>` — one template change fixes both the logged-out and
  logged-in nav, since they share it.
- Added a "Try the demo" panel to the login page
  (`registration/login.html`) showing both demo principals' real
  credentials from `load_demo_data.py`
  (`principal_riverside`/`principal_lincoln`, both `Demo-Pass-2026!`).
- Added a "Log in to explore the demo schedule" call-to-action to the
  public landing state of `schedule.html`, shown only to anonymous
  visitors.
- **Removed the Lessons list page and the Teacher Substitution page**
  as redundant: `LessonListView` and its `/lessons/` URL/nav item are
  gone (Lesson create/edit/delete, reached from the schedule page
  itself, are untouched — their redirect target changed from the
  removed list page to `schedule`). `TeacherSubstitutionView`/
  `TeacherSubstitutionForm`/its template/URL/nav item are gone; the
  underlying `SubstitutionService.available_teachers()` logic was left
  completely untouched (it has its own independent unit tests and
  wasn't reachable only from that page).
- **Deleted a dead "Default School"** from the real dev database: 80
  teachers named "Teacher 01"… "Teacher 80" and 2100 lessons, left over
  from the single-school version of `load_demo_data` and never cleaned
  up by any later migration. Backed up `db.sqlite3` first; deleted its
  `Lesson` rows before the `School` row itself, since `Lesson`'s FKs to
  Teacher/Room/Subject/StudentGroup/Period are `PROTECT` and would have
  blocked a cascading delete otherwise. Verified before and after that
  Riverside High and Lincoln Academy (the two real demo schools) were
  untouched.
- Updated/removed the tests that covered the removed pages
  (`test_web_pages.py`, `test_registration_view.py`,
  `test_crud_school_isolation.py`,
  `test_scheduling_school_isolation.py`).

### Verification performed

- `manage.py check` → no issues.
- `makemigrations --check --dry-run` → no changes detected (no schema
  change was made or needed).
- Full pytest suite → 323 passed, 0 failed (330 before this session;
  7 tests covered the two removed pages and were deleted, not
  skipped).
- Confirmed in a real browser: single nav link, demo CTA, both demo
  credentials visible on the login page.

### Current task

Implemented, verified, and committed (`a0b130e`).

### Next

Same as above: Phase 10 (testing audit), Phase 11 (production prep),
or Phase 13 (portfolio polish).

## 2026-10-09 — Phase 10: Testing & Quality Audit

### Completed (audit session, read-only)

Inspected all 42 test files, every view/form/service/model, and ran a
line-coverage report (`coverage`, installed temporarily in the venv
only, never added to `requirements.txt`, uninstalled afterward) to find
executed-but-unasserted branches. No code was changed in this session.
Headline finding: multi-school authorization/isolation is the
best-tested part of the codebase — no confirmed cross-school leak was
found. One confirmed defect was found (see below), plus a cluster of
real gaps concentrated in exception-handling branches and in the
2026-10-08 polish pass's own changes. Full findings, severity
classification, and file/line references are in the audit report
itself (not duplicated here — see the conversation history for the
complete report); the Phase 10 section above and this entry capture
the outcome, not the full writeup.

### Completed (implementation session)

- **Fixed the confirmed defect**: `ProtectedDeleteMixin` correctly
  blocked deletes of Lesson-referenced resources, but
  `object_confirm_delete.html` never rendered `form.non_field_errors`,
  so the user saw no explanation. Fixed with a 3-line template
  addition, mirroring the existing `object_form.html` convention.
  Verified empirically with a throwaway, non-persisted test before
  fixing (confirmed the exact symptom: 200, object survives, no error
  text in the response body) — deleted immediately after, never
  committed.
- **Removed confirmed dead code**: traced Django 5.2's
  `BaseDeleteView` MRO directly (`BaseDeleteView.post()` calls
  `self.form_valid()`, which dispatches to `ProtectedDeleteMixin`'s
  own override first) to prove `ProtectedDeleteMixin.post()`'s
  `except ProtectedError` handler could never fire. Removed it.
- **Added `tests/integration/test_protected_delete.py`**: the delete-
  blocked-with-error-shown regression test, parametrized across all
  six affected resource types (Teacher, Room, Subject, StudentGroup,
  Period, AcademicYear), plus one guard test that an unreferenced
  resource still deletes normally.
- **Closed the login/logout gap**: added 4 tests to
  `tests/integration/test_web_pages.py` — valid login redirects to
  `LOGIN_REDIRECT_URL` ("schedule"), invalid login shows Django's
  stock error and doesn't authenticate, logout redirects to
  `LOGOUT_REDIRECT_URL` ("login") and clears the session, and a
  protected page is denied immediately after logout. Verified the
  actual configured redirect targets in `config/settings.py` rather
  than assuming Django defaults.
- **Verified lesson redirect destinations**: added `response.url`
  assertions to the existing lesson create/update tests and one new
  lesson-delete test — these previously checked only `302`, which
  would not have caught the 2026-10-08 polish pass's redirect target
  silently pointing somewhere unintended.
- **Added open-redirect regression tests** for `_safe_next_url()`
  (`SchedulerCreateView`/`SchedulerUpdateView`): an unsafe scheme-
  relative/external `next` is rejected in favor of `list_url_name`; a
  safe internal `next` is still honored. Verified these tests are
  meaningful by temporarily neutering the check in both call sites,
  confirming both new "rejects" tests failed, then restoring the real
  implementation.
- **Added the `LessonWriteMixin.form_valid()` cross-school-error
  branch test**: this branch is structurally unreachable through a
  real form submission (`LessonForm`'s querysets are already scoped to
  the current school), so a narrowly-scoped `monkeypatch` of
  `build_schedule_service` (local to one test) was used to make the
  service raise `CrossSchoolLessonError`, proving the view catches it
  as a clean form error rather than a 500.
- **Deliberately not added**: a test for
  `GeneratePlannedSubstitutionsView`'s defense-in-depth
  `SchoolAuthorizationError` catch — it's a backstop behind an
  already-tested view-layer check, and the service-level guard it
  wraps already has its own tests in
  `tests/application/test_substitution_service.py`.
- **Cleaned up legacy duplicate tests**: `tests/test_teacher.py` and
  `tests/test_timeslot.py` (root-level, pre-reorganization) were not
  simply deleted — each contained one assertion not covered elsewhere
  (`Teacher.email` round-tripping; a valid domain `Period`'s fields all
  round-tripping together). Migrated both into their modern homes
  (`tests/infrastructure/test_resource_school_ownership.py`,
  `tests/domain/test_timeslot_validation.py`) before deleting the
  originals.

### Verification performed

- Full pytest suite → **339 passed, 0 failed** (330 → 339; +16 tests:
  +7 protected-delete, +4 login/logout, +1 lesson-delete-redirect,
  +3 open-redirect, +1 cross-school-error branch, +2 migrated from the
  2 deleted legacy files — net matches exactly).
- `manage.py check` → no issues.
- `makemigrations --check --dry-run` → no changes detected (no schema
  change was made or needed).
- `git diff --stat` reviewed: only
  `app/presentation/web/views.py` (11 lines, the dead-code removal) and
  `app/presentation/web/templates/scheduler/object_confirm_delete.html`
  (3 lines, the fix) outside the test suite — no unrelated files, no
  database changes, no new dependencies in `requirements.txt`.

### Current task

Phase 10 implemented and verified. Working tree uncommitted, pending
review.

### Next

Phase 11 (production prep) or Phase 13 (portfolio polish) — neither
scoped yet.

## 2026-10-10 — Phase 11: Production readiness audit, then PostgreSQL migration

### Completed (read-only audit, no changes)

Inspected `config/settings.py`, `requirements.txt`, `app/admin.py`,
templates, `.gitignore`, and git history; ran `manage.py check
--deploy` and a non-writing `collectstatic --dry-run --no-input`.
Findings (Critical unless noted): `DEBUG=True` hardcoded;
`SECRET_KEY` hardcoded to an obvious placeholder (checked its full git
history — never a real secret, so no retroactive exposure, just not
rotatable without a code change); `ALLOWED_HOSTS` empty (nothing would
serve in production until set); no HTTPS/cookie-security settings
(High); no `STATIC_ROOT` — `collectstatic` confirmed to fail outright;
no `LOGGING` config — confirmed via Django's own `DEFAULT_LOGGING`
that production errors would be completely silent (High); SQLite as
the only database, no production alternative wired up (High,
resolved below). Confirmed Django Admin has no row-level school
scoping (pre-existing, documented, explicitly out of scope to redesign
here) but that neither demo principal is `is_staff`, so neither can
reach it today — the only way that risk materializes is if a
staff/superuser account is deliberately created for maintenance, which
is a decision for the project owner, not a code defect.

### Completed (PostgreSQL migration)

Per explicit decision, PostgreSQL becomes the standard backend for
dev, test, and production — not a stopgap. No portability issues were
found requiring an architectural decision: no raw SQL, no
SQLite-specific fields/behavior, no backend-sensitive test assertions
anywhere in `app/` or `tests/` (confirmed by direct inspection, not
assumed).

- Backed up `db.sqlite3` to `backups/db.sqlite3.pre-postgres-backup-20261010`
  (new gitignored `backups/` directory) before touching anything;
  verified independently via raw `sqlite3` (`PRAGMA integrity_check` →
  `ok`) and a SHA-256 checksum match. The original `db.sqlite3` was
  confirmed byte-identical (same checksum) at the end of the session —
  never modified.
- Installed PostgreSQL 16 via Homebrew (approved explicitly before
  running) and started it as a background service. Created a
  dedicated `school_scheduler` role and `school_scheduler_dev`
  database (plus `CREATEDB` on the role — required for
  `pytest-django`'s automatic, isolated `test_<DB_NAME>` database;
  this is what makes "tests never touch the dev/production database"
  actually true rather than just configured).
- `config/settings.py`: `DATABASES` now reads `DB_NAME`/`DB_USER`/
  `DB_PASSWORD` (required, via a small `_required_env()` helper that
  raises `ImproperlyConfigured` naming the missing variable — verified
  empirically, not assumed) and `DB_HOST`/`DB_PORT` (optional,
  `localhost`/`5432`). `python-dotenv` loads a gitignored `.env` for
  local convenience; a real deployment sets the same variables
  directly. No other settings were touched — `SECRET_KEY`, `DEBUG`,
  and `ALLOWED_HOSTS` remain exactly as the audit found them.
- `requirements.txt`: added `psycopg[binary]` (the driver) and
  `python-dotenv`. Nothing else changed.
- Added `.env.example` (committed, no secrets) and a local `.env`
  (gitignored).
- Ran `migrate` against the fresh, empty Postgres database — all 12
  `app` migrations plus Django's own applied cleanly; schema verified
  directly (`\dt`, `\d app_lesson` — correct tables, FKs, indexes).
- Exported the real SQLite data with `dumpdata`, excluding
  `contenttypes`, `auth.permission`, `admin.logentry`, and
  `sessions.session` (Django-regenerated/ephemeral — importing them
  risks ID collisions with what `migrate` already created). Used a
  throwaway, untracked settings module to point `dumpdata` at the old
  SQLite file without touching the real (now Postgres-only)
  `config/settings.py`; deleted it immediately after. 1125 records
  exported (2 Schools, 3 Users, 2 SchoolMemberships, 2 AcademicYears,
  32 Teachers, 20 Rooms, 20 Subjects, 20 StudentGroups, 24 Periods,
  1000 Lessons) — an exact match for a direct query of the live
  SQLite database taken at the start of the session.
- Loaded all 1125 records into Postgres via `loaddata` — primary keys
  preserved exactly (School ids 2/3, membership ids 1/2, etc.).
  Confirmed Django's `loaddata` resets PostgreSQL sequences
  automatically after loading explicit PKs (read its source to
  verify, rather than assume) — then proved it empirically by creating
  and deleting a throwaway `School`/`Teacher` and confirming the new
  ids didn't collide with existing ones.

### Notable data finding

The database was **not** demo-data-only, as flagged before assuming
otherwise. Beyond the two demo schools (Riverside High, Lincoln
Academy) and their principals, there's an orphaned superuser account,
`principal` (user id 1, `is_staff=True`, `is_superuser=True`, **no**
`SchoolMembership`) — a leftover from early development, predating
even the "Default School" deleted in the 2026-10-08 polish pass. It
was preserved through the migration untouched, per instruction not to
clean up data during this work; its existence is now written down
here rather than silently carried forward.

### Verification performed

- `manage.py check`, `makemigrations --check --dry-run`, and
  `migrate --check` all clean, run twice (against the empty database
  and again after loading data).
- Full pytest suite against PostgreSQL → **339 passed**, 0 failed
  (159s — slower than SQLite's ~52s, as expected over a real
  connection; not a concern). Confirmed the ephemeral
  `test_school_scheduler_dev` database was created and destroyed
  automatically, and that `school_scheduler_dev` (the real dev
  database) had zero rows changed by the test run.
- Record counts compared directly, model by model — exact match
  between the original SQLite query and the migrated Postgres data
  (see above).
- `authenticate()` succeeded for both demo principals using their
  real, known passwords — confirms password hashes survived the
  dump/load round-trip, not just that rows exist.
- Direct ORM check: zero Lessons combine resources from different
  schools in the migrated data (the core multi-school integrity
  invariant), and `principal_riverside`'s only membership is Riverside
  High.
- HTTP-level check via `django.test.Client` against the real migrated
  dev database (not the ephemeral test database): login succeeded,
  the schedule page correctly showed "Riverside High", the scoped
  teacher list showed only Riverside's teachers, and a direct id-guess
  at a Lincoln Academy teacher's edit URL returned 404. Lesson
  creation/update and substitute generation were **not** additionally
  exercised against this real data (to avoid mutating the preserved
  dataset) — that behavior is already covered by the 339-test suite
  passing against this same Postgres setup.

### Files changed

`config/settings.py`, `requirements.txt`, `.gitignore` (added
`backups/`), `README.md` (new Database section), `PROJECT_CONTEXT.md`
(§3, §4 — SQLite→PostgreSQL), plus new `.env.example` (committed) and
`.env`/`backups/` (gitignored, not committed). No application,
domain, service, view, or template code was touched — this was
entirely configuration-layer, exactly as expected for a database
engine swap with no portability issues found.

### Current task

PostgreSQL migration implemented and verified for local development.
**Phase 11 is not complete** — `DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS`,
HTTPS/cookie settings, static files, and logging remain exactly as
the audit found them, unaddressed. Nothing has been committed.

### Next

Address the remaining Phase 11 audit findings (env-driven `DEBUG`/
`SECRET_KEY`/`ALLOWED_HOSTS`, HTTPS/cookie settings, `STATIC_ROOT` +
static serving, minimal `LOGGING`) before considering Phase 11 done,
or Phase 13 (portfolio polish) if that's prioritized first.
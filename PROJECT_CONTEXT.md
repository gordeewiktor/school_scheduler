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

`AcademicYear` is connected to `School` (required foreign key, see
§10). `Teacher`, `Room`, `Subject`, and `StudentGroup` are not yet
connected to `School` — that is Phase 3 (see §11–§12).

---

# 9. Current Database Relationships

The current conceptual structure is approximately:

    School
        │
        └── AcademicYear
                │
                └── Period

    Teacher
    Room
    Subject
    StudentGroup

    Lesson
        ├── Teacher
        ├── Subject
        ├── Room
        ├── StudentGroup
        ├── Period
        └── planned substitute Teacher

`School` and `SchoolMembership` exist (see §11–§12). `AcademicYear` now
has a required foreign key to `School` (see §10). `Teacher`, `Room`,
`Subject`, and `StudentGroup` are still unscoped — that is Phase 3, not
yet implemented.

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

Nothing else references `School` yet. `AcademicYear`, `Teacher`, `Room`,
`Subject`, and `StudentGroup` do not yet have a `school` foreign key —
that is Phase 2/3 of the roadmap, not yet implemented.

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

There is currently no "current school" resolution logic (no session/
request-level notion of "the school I'm acting as") — that is Phase 4
of the roadmap, not yet implemented. `SchoolMembership` rows are not
yet consulted anywhere outside the `create_school` management command
and admin.

A `create_school` management command exists to create a `School` and
attach an existing `User` to it as a principal
(`app/management/commands/create_school.py`). It has not been run
against the development database yet.

The important architectural decision is:

`is_staff` should NOT be used as the application's concept of school
ownership.

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

---

# 15. School-Owned Resources

The following resources are intended to belong directly to a School:

- Teacher
- Room
- Subject
- StudentGroup

These resources should be reusable across academic years.

For example, a teacher should not normally need to be recreated every
time a new academic year is created.

The intended relationship is:

    School
       ├── Teachers
       ├── Rooms
       ├── Subjects
       └── StudentGroups

Therefore, their names should eventually be unique within a School,
rather than globally.

For example:

    School A → Teacher "John Smith"
    School B → Teacher "John Smith"

should be valid.

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

A lesson does not currently have a direct School foreign key.

The initial multi-school design should avoid unnecessary denormalized
relationships.

Instead, the application should ensure that:

- the Lesson's AcademicYear belongs to the current School;
- the Teacher belongs to the same School;
- the Subject belongs to the same School;
- the Room belongs to the same School;
- the StudentGroup belongs to the same School;
- the Period belongs to the same School through its AcademicYear.

Cross-school references must be rejected.

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

The application uses a LessonRepository interface/Protocol.

Infrastructure contains a Django implementation, currently represented
by a Django lesson repository.

Repositories should eventually receive or otherwise operate within an
explicit school scope where appropriate.

Repository methods must not accidentally return data from other
schools.

For example, a method that retrieves teachers for substitution must
only consider teachers belonging to the current school.

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

---

# 21. Current Single-School Assumptions

The current code contains several assumptions that work only because
there is effectively one school.

Examples include:

- globally unique Teacher names;
- globally unique Room names;
- globally unique Subject names;
- globally unique StudentGroup names;
- globally unique AcademicYear names;
- unscoped repository queries;
- CRUD views querying all records;
- schedule selection using globally available AcademicYears;
- demo data assuming one school;
- no current-school context.

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

The next implementation step is:

    Connect Teacher, Room, Subject, and StudentGroup to School

Then:

    Enforce school-wide data isolation

Everything should be implemented incrementally and tested after each
meaningful change.
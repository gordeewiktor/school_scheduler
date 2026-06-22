PROJECT_BLUEPRINT.md

Purpose

This document defines the architectural principles, development practices, testing strategy, and project structure that should be followed in all future projects unless there is a strong reason not to.

The goal is to build software that is:

* Easy to understand
* Easy to test
* Easy to maintain
* Easy to extend
* Easy to refactor
* Professional enough for portfolio and production use

⸻

Core Philosophy

Rule 1: Business Logic Comes First

The most important code is the business logic.

Business rules must not depend on:

* Frameworks
* Databases
* APIs
* AI models
* File systems
* User interfaces

Business logic should remain usable even if all external technologies change.

Examples:

* Scheduling rules
* Reading-app scoring rules
* User progress calculations
* Conflict detection
* Validation rules

These belong in the core application.

⸻

Rule 2: Depend on Abstractions

High-level code should not depend on low-level code.

Use interfaces (ports) whenever external systems are involved.

Example:

Instead of:

ScheduleService → PostgreSQL

Use:

ScheduleService → ScheduleRepository

Then provide:

PostgresScheduleRepository

or

SQLiteScheduleRepository

or

InMemoryScheduleRepository

The service should not know which one is being used.

⸻

Rule 3: Infrastructure Stays at the Edge

External systems belong in infrastructure.

Examples:

* Database
* Email
* File system
* AI models
* External APIs
* Queue systems
* Cloud storage

Infrastructure code should never contain business rules.

Infrastructure exists only to communicate with the outside world.

⸻

Rule 4: Keep Services Thin and Focused

A service should coordinate a workflow.

A service should not become a “god object.”

Bad:

UserService
- create user
- send email
- generate reports
- process payments
- schedule meetings

Good:

UserService

PaymentService

NotificationService

ReportService

Each service should have a single responsibility.

⸻

Rule 5: Prefer Composition Over Inheritance

Favor dependency injection and composition.

Avoid deep inheritance hierarchies.

Good:

ScheduleService(
repository,
notifier
)

Avoid:

BaseService
-> AdvancedService
-> EnterpriseService
-> UltimateService

⸻

Architecture Standard

Preferred Architecture

Use a simplified Clean Architecture / Hexagonal Architecture approach.

Layers:

Domain
Application
Infrastructure
Presentation

Dependency direction:

Presentation
↓

Infrastructure
↓

Application
↓

Domain

The Domain layer must never depend on outer layers.

⸻

Recommended Folder Structure

app/

domain/
    entities/
    value_objects/
    policies/
    exceptions.py
application/
    services/
    ports/
infrastructure/
    database/
    repositories/
    integrations/
    notifications/
presentation/
    api/
    web/
main.py

tests/

domain/
application/
infrastructure/
integration/

docs/

README.md
PROJECT_BLUEPRINT.md

⸻

Domain Layer Rules

The domain layer contains:

* Business rules
* Entities
* Value objects
* Policies
* Domain exceptions

The domain layer must never:

* Import Django
* Import FastAPI
* Import SQLAlchemy
* Import database code
* Import API code

Domain code should be pure Python whenever possible.

⸻

Application Layer Rules

The application layer contains:

* Use cases
* Services
* Workflow orchestration

Examples:

ScheduleService

ConflictService

StudentProgressService

TranscriptionService

Responsibilities:

* Coordinate actions
* Call repositories
* Apply business rules

Responsibilities NOT allowed:

* SQL queries
* HTTP requests
* File writing

⸻

Infrastructure Layer Rules

Infrastructure contains:

* Database implementations
* Email implementations
* AI integrations
* External APIs
* File storage

Examples:

PostgresScheduleRepository

WhisperTranscriber

EmailNotificationSender

CSVImporter

Responsibilities:

* Technical implementation
* External communication

No business decisions belong here.

⸻

Presentation Layer Rules

Presentation includes:

* Django views
* FastAPI routes
* REST endpoints
* HTML pages

Presentation should be thin.

Good:

Request
→
Validation
→
Service
→
Response

Bad:

Request
→
500 lines of business logic
→
Response

⸻

Testing Philosophy

Testing is mandatory.

⸻

Unit Tests

Unit tests must be:

* Fast
* Isolated
* Deterministic

Unit tests should not require:

* Internet
* Database
* Filesystem
* External APIs

Most tests should be unit tests.

⸻

Integration Tests

Integration tests verify:

* Database connections
* API integrations
* AI integrations
* File operations

Keep only a small number.

Mark slow tests appropriately.

⸻

End-to-End Tests

Use only for critical workflows.

Example:

Create schedule
→ Validate conflicts
→ Save schedule
→ Display schedule

⸻

Testing Rules

Test business rules heavily.

Examples:

teacher_cannot_be_double_booked()

room_capacity_must_be_sufficient()

student_cannot_submit_twice()

These tests provide the highest value.

⸻

Dependency Injection Standard

Services receive dependencies through constructors.

Example:

class ScheduleService:

def __init__(
    self,
    repository,
    notifier,
    conflict_service
):
    self.repository = repository
    self.notifier = notifier
    self.conflict_service = conflict_service

Never instantiate infrastructure directly inside services.

Avoid:

repository = PostgresRepository()

inside business logic.

⸻

Error Handling

Fail loudly.

Raise meaningful exceptions.

Bad:

except:
pass

Good:

except FileNotFoundError:
raise AudioFileMissingError()

Business errors should have domain-specific exception names.

⸻

Code Quality Standards

Required:

* Type hints
* Meaningful names
* Small functions
* Small classes
* Consistent formatting

Recommended:

* Ruff
* Black
* Pytest
* MyPy

⸻

Git Standards

Never commit:

venv/

pycache/

.pytest_cache/

.env

generated files

temporary files

Always include:

.gitignore

README.md

requirements.txt or pyproject.toml

⸻

Documentation Standards

Every project should include:

README.md

Contents:

* Project description
* Features
* Installation
* Running instructions
* Test instructions
* Architecture overview

Complex decisions should be documented.

⸻

MVP Philosophy

Build the smallest useful version first.

Before adding:

* AI
* Notifications
* Optimization
* Complex UI
* Microservices

Ask:

“Does the user actually need this right now?”

Prefer:

Simple and working

over

Complex and unfinished

⸻

Portfolio Standards

Every project should demonstrate:

* Clean architecture
* Good testing
* Clear documentation
* Separation of concerns
* Professional Git history

A smaller polished project is better than a larger unfinished project.

⸻

Personal Development Goal

Every project should help improve:

* Python
* Testing
* Architecture
* Backend engineering skills

The objective is not only to finish projects.

The objective is to become a stronger software engineer with every project built.
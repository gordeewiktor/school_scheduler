import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

PRE_BACKFILL_MIGRATION = ("app", "0010_school_owned_resources_nullable")
BACKFILL_MIGRATION = ("app", "0011_backfill_school_owned_resources")


@pytest.mark.django_db(transaction=True)
def test_backfill_assigns_orphaned_resources_to_one_default_school():
    """Simulates pre-existing data (Teacher/Room/Subject/StudentGroup rows
    with no school, as on the real dev database before this migration) and
    verifies the data migration backfills all of them into a single
    "Default School" rather than losing or duplicating them."""
    executor = MigrationExecutor(connection)
    executor.migrate([PRE_BACKFILL_MIGRATION])

    old_apps = executor.loader.project_state([PRE_BACKFILL_MIGRATION]).apps
    OldTeacher = old_apps.get_model("app", "Teacher")
    OldRoom = old_apps.get_model("app", "Room")
    OldSubject = old_apps.get_model("app", "Subject")
    OldStudentGroup = old_apps.get_model("app", "StudentGroup")

    OldTeacher.objects.create(name="Legacy Teacher")
    OldRoom.objects.create(name="Legacy Room")
    OldSubject.objects.create(name="Legacy Subject")
    OldStudentGroup.objects.create(name="Legacy Group")

    executor = MigrationExecutor(connection)
    executor.migrate([BACKFILL_MIGRATION])

    new_apps = executor.loader.project_state([BACKFILL_MIGRATION]).apps
    NewSchool = new_apps.get_model("app", "School")
    NewTeacher = new_apps.get_model("app", "Teacher")
    NewRoom = new_apps.get_model("app", "Room")
    NewSubject = new_apps.get_model("app", "Subject")
    NewStudentGroup = new_apps.get_model("app", "StudentGroup")

    assert NewSchool.objects.count() == 1
    default_school = NewSchool.objects.get()
    assert default_school.name == "Default School"
    assert NewTeacher.objects.get(name="Legacy Teacher").school_id == default_school.id
    assert NewRoom.objects.get(name="Legacy Room").school_id == default_school.id
    assert NewSubject.objects.get(name="Legacy Subject").school_id == default_school.id
    assert NewStudentGroup.objects.get(name="Legacy Group").school_id == default_school.id

    # Restore the database to the latest migration state so later tests
    # in the suite see the schema they expect.
    executor = MigrationExecutor(connection)
    executor.migrate(executor.loader.graph.leaf_nodes())


@pytest.mark.django_db(transaction=True)
def test_backfill_reuses_an_existing_default_school_instead_of_duplicating_it():
    """Mirrors the real dev database: Phase 2's AcademicYear backfill
    already created a "Default School" before this migration runs. The
    Phase 3 backfill must reuse that exact row (so Teachers/Rooms/Subjects/
    StudentGroups end up owned by the same School as the existing
    AcademicYear and its Lessons), not create a second one."""
    executor = MigrationExecutor(connection)
    executor.migrate([PRE_BACKFILL_MIGRATION])

    old_apps = executor.loader.project_state([PRE_BACKFILL_MIGRATION]).apps
    OldSchool = old_apps.get_model("app", "School")
    OldTeacher = old_apps.get_model("app", "Teacher")
    OldRoom = old_apps.get_model("app", "Room")

    existing_default = OldSchool.objects.create(name="Default School")
    OldTeacher.objects.create(name="Legacy Teacher")
    OldRoom.objects.create(name="Legacy Room")

    executor = MigrationExecutor(connection)
    executor.migrate([BACKFILL_MIGRATION])

    new_apps = executor.loader.project_state([BACKFILL_MIGRATION]).apps
    NewSchool = new_apps.get_model("app", "School")
    NewTeacher = new_apps.get_model("app", "Teacher")
    NewRoom = new_apps.get_model("app", "Room")

    assert NewSchool.objects.count() == 1
    assert NewTeacher.objects.get(name="Legacy Teacher").school_id == existing_default.id
    assert NewRoom.objects.get(name="Legacy Room").school_id == existing_default.id

    executor = MigrationExecutor(connection)
    executor.migrate(executor.loader.graph.leaf_nodes())

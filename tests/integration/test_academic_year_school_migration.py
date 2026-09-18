import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

PRE_BACKFILL_MIGRATION = ("app", "0007_academicyear_school_nullable")
BACKFILL_MIGRATION = ("app", "0008_backfill_academicyear_school")


@pytest.mark.django_db(transaction=True)
def test_backfill_migration_assigns_orphaned_academic_years_to_default_school():
    """Simulates pre-existing data (an AcademicYear with no school, as on
    the real dev database before this migration) and verifies the data
    migration backfills it into a single "Default School" rather than
    losing or duplicating it."""
    executor = MigrationExecutor(connection)
    executor.migrate([PRE_BACKFILL_MIGRATION])

    old_apps = executor.loader.project_state([PRE_BACKFILL_MIGRATION]).apps
    OldAcademicYear = old_apps.get_model("app", "AcademicYear")
    OldAcademicYear.objects.create(name="Legacy Year", default_period_duration=45)

    executor = MigrationExecutor(connection)
    executor.migrate([BACKFILL_MIGRATION])

    new_apps = executor.loader.project_state([BACKFILL_MIGRATION]).apps
    NewAcademicYear = new_apps.get_model("app", "AcademicYear")
    NewSchool = new_apps.get_model("app", "School")

    year = NewAcademicYear.objects.get(name="Legacy Year")
    assert year.school_id is not None
    assert NewSchool.objects.count() == 1
    assert NewSchool.objects.get().name == "Default School"
    assert year.school_id == NewSchool.objects.get().id

    # Restore the database to the latest migration state so later tests
    # in the suite see the schema they expect.
    executor = MigrationExecutor(connection)
    executor.migrate(executor.loader.graph.leaf_nodes())


@pytest.mark.django_db(transaction=True)
def test_backfill_migration_reuses_one_default_school_for_multiple_years():
    executor = MigrationExecutor(connection)
    executor.migrate([PRE_BACKFILL_MIGRATION])

    old_apps = executor.loader.project_state([PRE_BACKFILL_MIGRATION]).apps
    OldAcademicYear = old_apps.get_model("app", "AcademicYear")
    OldAcademicYear.objects.create(name="Legacy Year A", default_period_duration=45)
    OldAcademicYear.objects.create(name="Legacy Year B", default_period_duration=45)

    executor = MigrationExecutor(connection)
    executor.migrate([BACKFILL_MIGRATION])

    new_apps = executor.loader.project_state([BACKFILL_MIGRATION]).apps
    NewSchool = new_apps.get_model("app", "School")
    NewAcademicYear = new_apps.get_model("app", "AcademicYear")

    assert NewSchool.objects.count() == 1
    school_ids = set(NewAcademicYear.objects.values_list("school_id", flat=True))
    assert school_ids == {NewSchool.objects.get().id}

    executor = MigrationExecutor(connection)
    executor.migrate(executor.loader.graph.leaf_nodes())

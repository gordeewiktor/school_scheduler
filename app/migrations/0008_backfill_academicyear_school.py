from django.db import migrations

DEFAULT_SCHOOL_NAME = "Default School"


def backfill_school(apps, schema_editor):
    School = apps.get_model("app", "School")
    AcademicYear = apps.get_model("app", "AcademicYear")

    orphaned_years = AcademicYear.objects.filter(school__isnull=True)
    if not orphaned_years.exists():
        return

    default_school, _ = School.objects.get_or_create(name=DEFAULT_SCHOOL_NAME)
    orphaned_years.update(school=default_school)


def noop_reverse(apps, schema_editor):
    # Intentionally not reversed: unassigning school_id would lose the
    # information this migration recorded, and the field is nullable at
    # this point in the migration history anyway.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0007_academicyear_school_nullable'),
    ]

    operations = [
        migrations.RunPython(backfill_school, noop_reverse),
    ]

from django.db import migrations

DEFAULT_SCHOOL_NAME = "Default School"


def backfill_school(apps, schema_editor):
    School = apps.get_model("app", "School")
    Teacher = apps.get_model("app", "Teacher")
    Room = apps.get_model("app", "Room")
    Subject = apps.get_model("app", "Subject")
    StudentGroup = apps.get_model("app", "StudentGroup")

    orphaned_querysets = [
        Teacher.objects.filter(school__isnull=True),
        Room.objects.filter(school__isnull=True),
        Subject.objects.filter(school__isnull=True),
        StudentGroup.objects.filter(school__isnull=True),
    ]
    if not any(queryset.exists() for queryset in orphaned_querysets):
        return

    default_school, _ = School.objects.get_or_create(name=DEFAULT_SCHOOL_NAME)
    for queryset in orphaned_querysets:
        queryset.update(school=default_school)


def noop_reverse(apps, schema_editor):
    # Intentionally not reversed: unassigning school_id would lose the
    # information this migration recorded, and the field is nullable at
    # this point in the migration history anyway.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0010_school_owned_resources_nullable'),
    ]

    operations = [
        migrations.RunPython(backfill_school, noop_reverse),
    ]

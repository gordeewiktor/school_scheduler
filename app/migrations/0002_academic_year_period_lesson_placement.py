import django.db.models.deletion
from django.db import migrations, models


def migrate_time_slots(apps, schema_editor):
    AcademicYear = apps.get_model("app", "AcademicYear")
    Period = apps.get_model("app", "Period")
    TimeSlot = apps.get_model("app", "TimeSlot")
    Lesson = apps.get_model("app", "Lesson")

    if not TimeSlot.objects.exists():
        return

    year = AcademicYear.objects.create(name="Legacy")
    intervals = sorted(
        set(TimeSlot.objects.values_list("start_time", "end_time")),
        key=lambda interval: (interval[0], interval[1]),
    )
    periods = {}
    for order, (start_time, end_time) in enumerate(intervals, start=1):
        periods[(start_time, end_time)] = Period.objects.create(
            academic_year=year,
            name=f"Period {order}",
            order=order,
            start_time=start_time,
            end_time=end_time,
            kind="LESSON",
        )

    weekdays = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday"}
    for lesson in Lesson.objects.select_related("time_slot"):
        if lesson.time_slot.day not in weekdays:
            raise RuntimeError(
                "Weekend lessons must be removed or moved to a weekday before this migration."
            )
        lesson.day = lesson.time_slot.day.upper()
        lesson.start_period = periods[
            (lesson.time_slot.start_time, lesson.time_slot.end_time)
        ]
        lesson.duration = 1
        lesson.save(update_fields=["day", "start_period", "duration"])


class Migration(migrations.Migration):
    dependencies = [("app", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="AcademicYear",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=40, unique=True)),
            ],
            options={"ordering": ["-name"]},
        ),
        migrations.CreateModel(
            name="Period",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=80)),
                ("order", models.PositiveIntegerField()),
                ("start_time", models.TimeField()),
                ("end_time", models.TimeField()),
                (
                    "kind",
                    models.CharField(
                        choices=[("LESSON", "Lesson"), ("BREAK", "Break")],
                        default="LESSON",
                        max_length=10,
                    ),
                ),
                (
                    "academic_year",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="periods",
                        to="app.academicyear",
                    ),
                ),
            ],
            options={"ordering": ["academic_year", "order"]},
        ),
        migrations.AddField(
            model_name="lesson",
            name="day",
            field=models.CharField(
                blank=True,
                choices=[
                    ("MONDAY", "Monday"),
                    ("TUESDAY", "Tuesday"),
                    ("WEDNESDAY", "Wednesday"),
                    ("THURSDAY", "Thursday"),
                    ("FRIDAY", "Friday"),
                ],
                max_length=9,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="lesson",
            name="duration",
            field=models.PositiveSmallIntegerField(default=1),
        ),
        migrations.AddField(
            model_name="lesson",
            name="start_period",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="starting_lessons",
                to="app.period",
            ),
        ),
        migrations.RunPython(migrate_time_slots, migrations.RunPython.noop),
        migrations.RemoveField(model_name="lesson", name="time_slot"),
        migrations.DeleteModel(name="TimeSlot"),
        migrations.AlterField(
            model_name="lesson",
            name="day",
            field=models.CharField(
                choices=[
                    ("MONDAY", "Monday"),
                    ("TUESDAY", "Tuesday"),
                    ("WEDNESDAY", "Wednesday"),
                    ("THURSDAY", "Thursday"),
                    ("FRIDAY", "Friday"),
                ],
                max_length=9,
            ),
        ),
        migrations.AlterField(
            model_name="lesson",
            name="start_period",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="starting_lessons",
                to="app.period",
            ),
        ),
        migrations.AlterModelOptions(
            name="lesson",
            options={
                "ordering": [
                    "day",
                    "start_period__order",
                    "student_group__name",
                    "subject__name",
                ]
            },
        ),
        migrations.AddConstraint(
            model_name="period",
            constraint=models.UniqueConstraint(
                fields=("academic_year", "order"), name="unique_period_order_per_year"
            ),
        ),
        migrations.AddConstraint(
            model_name="period",
            constraint=models.UniqueConstraint(
                fields=("academic_year", "name"), name="unique_period_name_per_year"
            ),
        ),
    ]

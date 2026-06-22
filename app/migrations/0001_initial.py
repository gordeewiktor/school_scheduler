import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Room",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80, unique=True)),
                ("capacity", models.PositiveIntegerField(blank=True, null=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="StudentGroup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True)),
                ("size", models.PositiveIntegerField(blank=True, null=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Subject",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True)),
                ("code", models.CharField(blank=True, max_length=30)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Teacher",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True)),
                ("email", models.EmailField(blank=True, max_length=254)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="TimeSlot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "day",
                    models.CharField(
                        choices=[
                            ("Monday", "Monday"),
                            ("Tuesday", "Tuesday"),
                            ("Wednesday", "Wednesday"),
                            ("Thursday", "Thursday"),
                            ("Friday", "Friday"),
                            ("Saturday", "Saturday"),
                            ("Sunday", "Sunday"),
                        ],
                        max_length=12,
                    ),
                ),
                ("start_time", models.TimeField()),
                ("end_time", models.TimeField()),
            ],
            options={"ordering": ["day", "start_time"]},
        ),
        migrations.CreateModel(
            name="Lesson",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("notes", models.TextField(blank=True)),
                (
                    "room",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="lessons", to="app.room"),
                ),
                (
                    "student_group",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="lessons", to="app.studentgroup"),
                ),
                (
                    "subject",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="lessons", to="app.subject"),
                ),
                (
                    "teacher",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="lessons", to="app.teacher"),
                ),
                (
                    "time_slot",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="lessons", to="app.timeslot"),
                ),
            ],
            options={
                "ordering": [
                    "time_slot__day",
                    "time_slot__start_time",
                    "student_group__name",
                    "subject__name",
                ]
            },
        ),
        migrations.AddConstraint(
            model_name="timeslot",
            constraint=models.UniqueConstraint(fields=("day", "start_time", "end_time"), name="unique_time_slot"),
        ),
    ]

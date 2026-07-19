from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0004_lesson_planned_substitute"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="lesson",
            name="duration",
        ),
    ]

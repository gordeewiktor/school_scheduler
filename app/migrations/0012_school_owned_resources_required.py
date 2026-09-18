import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0011_backfill_school_owned_resources'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='teacher',
            options={'ordering': ['school', 'name']},
        ),
        migrations.AlterModelOptions(
            name='room',
            options={'ordering': ['school', 'name']},
        ),
        migrations.AlterModelOptions(
            name='subject',
            options={'ordering': ['school', 'name']},
        ),
        migrations.AlterModelOptions(
            name='studentgroup',
            options={'ordering': ['school', 'name']},
        ),
        migrations.AlterField(
            model_name='teacher',
            name='name',
            field=models.CharField(max_length=120),
        ),
        migrations.AlterField(
            model_name='room',
            name='name',
            field=models.CharField(max_length=80),
        ),
        migrations.AlterField(
            model_name='subject',
            name='name',
            field=models.CharField(max_length=120),
        ),
        migrations.AlterField(
            model_name='studentgroup',
            name='name',
            field=models.CharField(max_length=120),
        ),
        migrations.AlterField(
            model_name='teacher',
            name='school',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teachers', to='app.school'),
        ),
        migrations.AlterField(
            model_name='room',
            name='school',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rooms', to='app.school'),
        ),
        migrations.AlterField(
            model_name='subject',
            name='school',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subjects', to='app.school'),
        ),
        migrations.AlterField(
            model_name='studentgroup',
            name='school',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_groups', to='app.school'),
        ),
        migrations.AddConstraint(
            model_name='teacher',
            constraint=models.UniqueConstraint(fields=('school', 'name'), name='unique_teacher_name_per_school'),
        ),
        migrations.AddConstraint(
            model_name='room',
            constraint=models.UniqueConstraint(fields=('school', 'name'), name='unique_room_name_per_school'),
        ),
        migrations.AddConstraint(
            model_name='subject',
            constraint=models.UniqueConstraint(fields=('school', 'name'), name='unique_subject_name_per_school'),
        ),
        migrations.AddConstraint(
            model_name='studentgroup',
            constraint=models.UniqueConstraint(fields=('school', 'name'), name='unique_student_group_name_per_school'),
        ),
    ]

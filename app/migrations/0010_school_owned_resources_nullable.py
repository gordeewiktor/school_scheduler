import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0009_academicyear_school_required'),
    ]

    operations = [
        migrations.AddField(
            model_name='teacher',
            name='school',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='teachers', to='app.school'),
        ),
        migrations.AddField(
            model_name='room',
            name='school',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='rooms', to='app.school'),
        ),
        migrations.AddField(
            model_name='subject',
            name='school',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subjects', to='app.school'),
        ),
        migrations.AddField(
            model_name='studentgroup',
            name='school',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='student_groups', to='app.school'),
        ),
    ]

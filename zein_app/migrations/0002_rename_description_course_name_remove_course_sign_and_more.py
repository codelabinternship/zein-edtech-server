# Generated by Django 5.2 on 2025-05-14 11:42

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zein_app', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='course',
            old_name='description',
            new_name='name',
        ),
        migrations.RemoveField(
            model_name='course',
            name='Sign',
        ),
        migrations.RemoveField(
            model_name='course',
            name='duration_months',
        ),
        migrations.RemoveField(
            model_name='course',
            name='level',
        ),
        migrations.RemoveField(
            model_name='course',
            name='price',
        ),
        migrations.RemoveField(
            model_name='course',
            name='title',
        ),
        migrations.AlterField(
            model_name='course',
            name='language',
            field=models.CharField(default='ru', max_length=10),
        ),
        migrations.CreateModel(
            name='CourseLevel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('level', models.CharField(choices=[('A1-A2', 'A1-A2'), ('B1-B2', 'B1-B2'), ('C1-C2', 'C1-C2')], max_length=10)),
                ('duration_months', models.CharField(max_length=20)),
                ('price', models.DecimalField(decimal_places=2, max_digits=12)),
                ('features', models.JSONField(default=list)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='levels', to='zein_app.course')),
            ],
        ),
    ]

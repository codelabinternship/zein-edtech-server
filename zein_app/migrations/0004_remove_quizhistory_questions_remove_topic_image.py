# Generated by Django 5.2 on 2025-06-03 03:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zein_app', '0003_quizhistory_questions'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='quizhistory',
            name='questions',
        ),
        migrations.RemoveField(
            model_name='topic',
            name='image',
        ),
    ]

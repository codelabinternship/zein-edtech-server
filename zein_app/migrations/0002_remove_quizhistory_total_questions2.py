# Generated by Django 5.2 on 2025-06-02 15:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zein_app', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='quizhistory',
            name='total_questions2',
        ),
    ]

# Generated by Django 5.2 on 2025-05-21 12:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zein_app', '0013_alter_result_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='result',
            name='image',
            field=models.ImageField(default='/placeholder.svg', upload_to='exam-results/'),
        ),
    ]

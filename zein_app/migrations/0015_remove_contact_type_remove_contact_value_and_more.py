# Generated by Django 5.2 on 2025-05-21 22:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zein_app', '0014_alter_result_image'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contact',
            name='type',
        ),
        migrations.RemoveField(
            model_name='contact',
            name='value',
        ),
        migrations.AddField(
            model_name='contact',
            name='email',
            field=models.EmailField(default='', max_length=255, unique=True),
        ),
        migrations.AddField(
            model_name='contact',
            name='hero_banner',
            field=models.ImageField(null=True, upload_to='contact/banner/'),
        ),
        migrations.AddField(
            model_name='contact',
            name='instagram',
            field=models.CharField(default='instagram.com/', max_length=255),
        ),
        migrations.AddField(
            model_name='contact',
            name='phone',
            field=models.CharField(default='+998', max_length=255, unique=True),
        ),
        migrations.AddField(
            model_name='contact',
            name='telegram',
            field=models.CharField(default='t.me/', max_length=255),
        ),
    ]

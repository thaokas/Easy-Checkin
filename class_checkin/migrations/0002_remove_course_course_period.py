# Generated by Django 5.1.3 on 2025-01-06 12:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('class_checkin', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='course',
            name='course_period',
        ),
    ]

# Generated by Django 4.2 on 2023-06-17 16:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0002_rename_first_name_user_name_remove_user_last_name_and_more")
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="uwhatsapp",
            field=models.CharField(blank=True, max_length=15, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="whatsapp",
            field=models.CharField(blank=True, max_length=15, null=True),
        ),
    ]

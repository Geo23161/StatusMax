# Generated by Django 4.2 on 2023-07-21 04:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [("app", "0016_userstories_picture")]

    operations = [
        migrations.CreateModel(
            name="CibleF",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("ip_address", models.CharField(blank=True, max_length=150, null=True)),
                ("created", models.DateTimeField(auto_now=True)),
                (
                    "interests",
                    models.ManyToManyField(
                        blank=True, null=True, related_name="cibles", to="app.interest"
                    ),
                ),
                (
                    "story",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cibles",
                        to="app.userstories",
                    ),
                ),
            ],
        )
    ]

# Generated by Django 4.2 on 2023-06-21 21:28

import cloudinary.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [("app", "0005_remove_userstories_a_interest_and_more")]

    operations = [
        migrations.CreateModel(
            name="Campaign",
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
                ("quart", models.TextField(blank=True, null=True)),
                ("min_age", models.IntegerField(default=18)),
                ("max_age", models.IntegerField(default=50)),
                ("sex", models.CharField(default="all", max_length=10)),
                ("currency", models.CharField(default="XOF", max_length=10)),
                ("days", models.IntegerField(default=1)),
                ("total_invest", models.IntegerField(default=0)),
                ("already_used", models.IntegerField(default=0)),
                ("enchere", models.IntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="MediaPost",
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
                ("image", models.ImageField(upload_to="images/")),
                (
                    "video",
                    cloudinary.models.CloudinaryField(
                        blank=True, max_length=255, null=True
                    ),
                ),
                ("name", models.CharField(blank=True, max_length=150, null=True)),
            ],
        ),
        migrations.AddField(
            model_name="userstories",
            name="price",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="Post",
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
                ("text", models.TextField(blank=True, null=True)),
                ("url", models.TextField(blank=True, null=True)),
                (
                    "campaign",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="posts",
                        to="app.campaign",
                    ),
                ),
                (
                    "media",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="in_posts",
                        to="app.mediapost",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Company",
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
                ("name", models.CharField(blank=True, max_length=150, null=True)),
                ("description", models.TextField(blank=True, null=True)),
                (
                    "creator",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "users",
                    models.ManyToManyField(
                        blank=True,
                        null=True,
                        related_name="company_in",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="campaign",
            name="company",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="campaignes",
                to="app.company",
            ),
        ),
        migrations.AddField(
            model_name="campaign",
            name="interests",
            field=models.ManyToManyField(
                related_name="in_campaigns", to="app.interest"
            ),
        ),
        migrations.AddField(
            model_name="campaign",
            name="professions",
            field=models.ManyToManyField(
                related_name="in_campaigns", to="app.profession"
            ),
        ),
        migrations.CreateModel(
            name="AcceptedPost",
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
                ("goals", models.IntegerField(default=10)),
                (
                    "preuve",
                    models.ImageField(blank=True, null=True, upload_to="preuves/"),
                ),
                ("checked", models.BooleanField(default=False)),
                ("payed", models.BooleanField(default=False)),
                (
                    "post",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="accepted_stories",
                        to="app.post",
                    ),
                ),
                (
                    "story",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="accepted_posts",
                        to="app.userstories",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="userstories",
            name="proposed_posts",
            field=models.ManyToManyField(related_name="in_stories", to="app.post"),
        ),
    ]

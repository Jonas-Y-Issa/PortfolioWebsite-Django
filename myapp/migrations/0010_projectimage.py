from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("myapp", "0009_project_http_links")]

    operations = [
        migrations.CreateModel(
            name="ProjectImage",
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
                (
                    "image",
                    models.CharField(
                        help_text="Image filename relative to homepage/images/.",
                        max_length=200,
                    ),
                ),
                ("caption", models.CharField(max_length=150)),
                ("position", models.PositiveIntegerField(default=0)),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="gallery",
                        to="myapp.project",
                    ),
                ),
            ],
            options={"ordering": ["position", "pk"]},
        ),
    ]

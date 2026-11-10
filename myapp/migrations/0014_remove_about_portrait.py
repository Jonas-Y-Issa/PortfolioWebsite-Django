from django.db import migrations, models


RETIRED_CAPTION = "Felsensteg Birg · Lauterbrunnen, Switzerland (2022)"


def remove_about_portrait(apps, schema_editor):
    About = apps.get_model("myapp", "About")
    portraits = About.objects.using(schema_editor.connection.alias).filter(
        image="profile.jpeg"
    )
    portraits.filter(image_desc=RETIRED_CAPTION).update(image_desc="")
    portraits.update(image="")


class Migration(migrations.Migration):
    dependencies = [("myapp", "0013_remove_chess_results")]

    operations = [
        migrations.AlterField(
            model_name="about",
            name="image",
            field=models.ImageField(blank=True, upload_to=""),
        ),
        migrations.AlterField(
            model_name="about",
            name="image_desc",
            field=models.CharField(blank=True, max_length=100),
        ),
        # Restore a database backup to recover the retired image references.
        migrations.RunPython(remove_about_portrait),
    ]

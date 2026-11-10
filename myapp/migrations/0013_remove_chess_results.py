from django.db import migrations
from django.db.models import Q


def remove_chess_results(apps, schema_editor):
    ProjectImage = apps.get_model("myapp", "ProjectImage")
    chess_url = "https://github.com/Jonas-Y-Issa/4-Way-Chess"
    ProjectImage.objects.using(schema_editor.connection.alias).filter(
        Q(project__extLink__iexact=chess_url)
        | Q(project__extLink__iexact=f"{chess_url}/"),
        image="chess-results.png",
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("myapp", "0012_remove_chess_colour_selection")]

    # Restore a database backup to recover deleted gallery content.
    operations = [migrations.RunPython(remove_chess_results)]

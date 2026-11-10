from django.db import migrations
from django.db.models import Q


def remove_colour_selection(apps, schema_editor):
    ProjectImage = apps.get_model("myapp", "ProjectImage")
    chess_url = "https://github.com/Jonas-Y-Issa/4-Way-Chess"
    ProjectImage.objects.using(schema_editor.connection.alias).filter(
        Q(project__extLink__iexact=chess_url)
        | Q(project__extLink__iexact=f"{chess_url}/"),
        image="chess-colour-selection.png",
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("myapp", "0011_refresh_portfolio_projects")]

    operations = [migrations.RunPython(remove_colour_selection)]

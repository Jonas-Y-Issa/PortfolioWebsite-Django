from django.db import migrations
from django.db.models import Q


CHESS_URL = "https://github.com/Jonas-Y-Issa/4-Way-Chess"
OLD_PORTFOLIO_URL = "https://github.com/Jonas-Y-Issa/PortfolioWebsite"
CHESS_IMAGES = [
    ("chess-gameplay.png", "Four-player chess in progress"),
    ("chess-menu.png", "Main menu"),
    ("chess-colour-selection.png", "Player colour selection"),
    ("chess-results.png", "Match results"),
]


def refresh_projects(apps, schema_editor):
    Project = apps.get_model("myapp", "Project")
    ProjectImage = apps.get_model("myapp", "ProjectImage")
    database = schema_editor.connection.alias

    chess_projects = Project.objects.using(database).filter(
        Q(extLink__iexact=CHESS_URL) | Q(extLink__iexact=f"{CHESS_URL}/")
    )
    for project in chess_projects:
        project.image = "chess-gameplay.png"
        project.save(using=database, update_fields=["image"])
        for position, (image, caption) in enumerate(CHESS_IMAGES):
            ProjectImage.objects.using(database).update_or_create(
                project_id=project.pk,
                image=image,
                defaults={"caption": caption, "position": position},
            )

    Project.objects.using(database).filter(
        Q(extLink__iexact=OLD_PORTFOLIO_URL)
        | Q(extLink__iexact=f"{OLD_PORTFOLIO_URL}/"),
        title="Portfolio Website Github",
        image="pi.jpeg",
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("myapp", "0010_projectimage")]

    # Deleted project content and the previous cover cannot be reconstructed.
    # Restore a database backup if this content migration must be rolled back.
    operations = [migrations.RunPython(refresh_projects)]

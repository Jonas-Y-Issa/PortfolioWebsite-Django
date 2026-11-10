from django.core.validators import URLValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("myapp", "0008_apps")]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="extLink",
            field=models.URLField(validators=[URLValidator(schemes=["http", "https"])]),
        ),
    ]

import shutil
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
from zipfile import ZipFile

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from myapp.models import About, Project, ProjectImage


class PagesExportTests(TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.settings_override = self.settings(BASE_DIR=self.root)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.project = Project.objects.create(
            inc=1, preface="Game", title="Public chess project",
            extLink="https://example.com/chess", description="Public project story.",
            image="chess-gameplay.png",
        )
        ProjectImage.objects.create(
            project=self.project, image="chess-menu.png", caption="Public chess menu",
        )
        About.objects.create(description="Public biography.")
        self.output = self.root / "build/pages"
        self.archive = self.root / "build/pages.zip"

    def export(self):
        call_command("export_pages", stdout=StringIO())

    def test_exports_public_content_and_assets_with_zip_at_root(self):
        get_user_model().objects.create_user("private-admin", password="not-for-public-output")
        for name in (".env", "db.sqlite3", "secret.py"):
            (self.root / name).write_text("PRIVATE-SENTINEL")
        self.export()

        html = (self.output / "index.html").read_text()
        self.assertIn("Public chess project", html)
        self.assertIn("Public biography.", html)
        self.assertIn("Public chess menu", html)
        self.assertIn("Page not found", (self.output / "404.html").read_text())
        self.assertIn("/favicon.ico /static/base/images/favicon.svg 301", (self.output / "_redirects").read_text())
        self.assertTrue((self.output / "static/base/scripts/portfolio.js").is_file())
        self.assertTrue((self.output / "static/base/fonts/EBGaramond.ttf").is_file())
        with ZipFile(self.archive) as bundle:
            names = bundle.namelist()
            self.assertIn("index.html", names)
            self.assertIn("static/homepage/images/chess-menu.png", names)
            self.assertEqual(set(names), {p.relative_to(self.output).as_posix()
                                         for p in self.output.rglob("*") if p.is_file()})
            self.assertFalse(any("admin" in name or ".sqlite" in name or name.endswith(".py")
                                 or name.startswith(".") for name in names))
            self.assertNotIn(b"PRIVATE-SENTINEL", b"".join(bundle.read(name) for name in names))
        self.assertNotIn("private-admin", html)

    def test_missing_image_preserves_previous_export_and_zip(self):
        self.export()
        original_html, original_zip = (self.output / "index.html").read_bytes(), self.archive.read_bytes()
        self.project.gallery.update(image="missing-image.png")
        with self.assertRaisesMessage(CommandError, "Missing or invalid public asset"):
            self.export()
        self.assertEqual((self.output / "index.html").read_bytes(), original_html)
        self.assertEqual(self.archive.read_bytes(), original_zip)

    def test_successful_reexport_replaces_stale_generated_files(self):
        self.export()
        (self.output / "stale.txt").write_text("old build artifact")
        self.project.title = "Updated public title"
        self.project.save()
        self.export()
        self.assertIn("Updated public title", (self.output / "index.html").read_text())
        self.assertFalse((self.output / "stale.txt").exists())

    def test_missing_database_is_not_created(self):
        missing = self.root / "missing.sqlite3"
        database = {"ENGINE": "django.db.backends.sqlite3", "NAME": missing}
        with patch("myapp.management.commands.export_pages.connections",
                   {"default": SimpleNamespace(settings_dict=database)}):
            with self.assertRaisesMessage(CommandError, "database does not exist"):
                self.export()
        self.assertFalse(missing.exists())
        self.assertFalse(self.output.exists())

    def test_empty_database_does_not_publish_placeholder_site(self):
        Project.objects.all().delete()
        with self.assertRaisesMessage(CommandError, "No projects found"):
            self.export()
        self.assertFalse(self.output.exists())

    def test_unowned_output_is_preserved(self):
        self.output.mkdir(parents=True)
        important = self.output / "keep.txt"
        important.write_text("keep")
        with self.assertRaisesMessage(CommandError, "not an owned export"):
            self.export()
        self.assertEqual(important.read_text(), "keep")

    def test_symlink_destinations_are_rejected(self):
        target = self.root / "external"
        target.mkdir()
        (self.root / "build").symlink_to(target, target_is_directory=True)
        with self.assertRaisesMessage(CommandError, "symlink in the export destination"):
            self.export()
        self.assertEqual(list(target.iterdir()), [])

    def test_public_source_symlinks_are_rejected(self):
        app = self.root / "fake-app"
        assets = app / "static/base"
        assets.mkdir(parents=True)
        private = self.root / "private.txt"
        private.write_text("private")
        (assets / "public.css").symlink_to(private)
        with patch("myapp.management.commands.export_pages.apps.get_app_config",
                   return_value=SimpleNamespace(path=app)):
            with self.assertRaisesMessage(CommandError, "symlink in public assets"):
                self.export()
        self.assertFalse(self.output.exists())
    def test_private_static_files_are_excluded_and_missing_css_assets_fail(self):
        app = self.root / "fake-app"
        source = Path(apps.get_app_config("myapp").path) / "static"
        shutil.copytree(source, app / "static")
        for name in (".env", "private.py", "db.sqlite3", ".hidden.css"):
            (app / "static/base" / name).write_text("PRIVATE-SENTINEL")
        with patch("myapp.management.commands.export_pages.apps.get_app_config",
                   return_value=SimpleNamespace(path=app)):
            self.export()
            self.assertFalse(any(p.name in {".env", "private.py", "db.sqlite3", ".hidden.css"}
                                 for p in self.output.rglob("*")))
            previous = self.archive.read_bytes()
            (app / "static/base/fonts/Liberation-Mono.ttf").unlink()
            with self.assertRaisesMessage(CommandError, "Liberation-Mono.ttf"):
                self.export()
            self.assertEqual(self.archive.read_bytes(), previous)

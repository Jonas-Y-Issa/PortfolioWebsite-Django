"""Export the public portfolio, without its database or Django administration."""

import re
import shutil
from html.parser import HTMLParser
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import parse_qs, unquote, urljoin, urlsplit
from zipfile import ZIP_DEFLATED, ZipFile

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.management.base import BaseCommand, CommandError
from django.db import connections
from django.template.loader import render_to_string
from django.test import RequestFactory, override_settings

from myapp.models import Project
from myapp.views import index


ASSET_EXTENSIONS = {
    ".css", ".js", ".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp",
    ".avif", ".ico", ".ttf", ".woff", ".woff2", ".eot",
}
MARKER = "Django-Portfolio Cloudflare Pages export v1\n"
CSS_URL = re.compile(r"url\(\s*['\"]?([^'\"\)]+?)['\"]?\s*\)", re.IGNORECASE)


class AssetReferences(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attributes):
        self.urls.extend(value for name, value in attributes
                         if name in {"src", "href", "poster"} and value)


class Command(BaseCommand):
    help = "Export public HTML and assets to build/pages/ and build/pages.zip."
    requires_system_checks = []

    def handle(self, *args, **options):
        self.check_database()
        if not Project.objects.exists():
            raise CommandError("No projects found. Populate the local portfolio before exporting.")

        build = Path(settings.BASE_DIR) / "build"
        output, archive, marker = build / "pages", build / "pages.zip", build / ".pages-export"
        self.check_destination(build, output, archive, marker)
        build.mkdir(exist_ok=True)

        # Render, validate and zip everything before touching the previous export.
        with TemporaryDirectory(prefix=".pages-stage-", dir=build) as temporary:
            stage = Path(temporary) / "pages"
            stage.mkdir()
            request = RequestFactory().get("/", HTTP_HOST="localhost")
            request.user = AnonymousUser()
            with override_settings(STATIC_URL="/static/"):
                (stage / "index.html").write_bytes(index(request).content)
                (stage / "404.html").write_text(
                    render_to_string("404.html", request=request), encoding="utf-8",
                )
            self.copy_assets(stage)
            (stage / "_redirects").write_text(
                "/favicon.ico /static/base/images/favicon.svg 301\n", encoding="utf-8",
            )
            self.validate_references(stage)
            files = sorted(path for path in stage.rglob("*") if path.is_file())
            if len(files) > 1000 or any(path.stat().st_size > 25 * 1024 * 1024 for path in files):
                raise CommandError("Export exceeds Cloudflare dashboard upload limits (1,000 files, 25 MiB each).")
            staged_archive = Path(temporary) / "pages.zip"
            with ZipFile(staged_archive, "w", ZIP_DEFLATED) as bundle:
                for path in files:
                    bundle.write(path, path.relative_to(stage).as_posix())

            # The marker is outside the published directory and ZIP.
            marker.write_text(MARKER, encoding="utf-8")
            previous = Path(temporary) / "previous"
            if output.exists():
                output.rename(previous)
            try:
                stage.rename(output)
                staged_archive.replace(archive)
            except OSError:
                if output.exists():
                    shutil.rmtree(output)
                if previous.exists():
                    previous.rename(output)
                raise

        self.stdout.write(self.style.SUCCESS(
            f"Exported {len(files)} public files to {output}\nUpload {archive} to Cloudflare Pages."
        ))

    @staticmethod
    def check_database():
        database = connections["default"].settings_dict
        if database["ENGINE"] != "django.db.backends.sqlite3":
            return
        name = str(database["NAME"])
        if name == ":memory:":
            return
        parsed = urlsplit(name) if name.startswith("file:") else None
        if parsed and parse_qs(parsed.query).get("mode") == ["memory"]:
            return
        path = Path(unquote(parsed.path) if parsed else name)
        if not path.is_file():
            raise CommandError(f"The portfolio database does not exist: {path}. Restore it before exporting.")

    @staticmethod
    def check_destination(build, output, archive, marker):
        for path in (build, *build.parents, output, archive, marker):
            if path.is_symlink():
                raise CommandError(f"Refusing a symlink in the export destination: {path}")
        if build.exists() and not build.is_dir():
            raise CommandError(f"Export build path is not a directory: {build}")
        if output.exists() and not output.is_dir():
            raise CommandError(f"Export output is not a directory: {output}")
        if archive.exists() and not archive.is_file():
            raise CommandError(f"Export ZIP path is not a file: {archive}")
        if marker.exists() and (not marker.is_file() or marker.read_text() != MARKER):
            raise CommandError(f"Unrecognized export ownership marker: {marker}")
        if (output.exists() or archive.exists()) and not marker.exists():
            raise CommandError("Existing build/pages or build/pages.zip is not an owned export; move it first.")

    @staticmethod
    def copy_assets(stage):
        source = Path(apps.get_app_config("myapp").path) / "static"
        if source.is_symlink():
            raise CommandError(f"Refusing a symlink in public assets: {source}")
        for namespace in ("base", "homepage"):
            root = source / namespace
            for path in (root, *sorted(root.rglob("*"))):
                if path.is_symlink():
                    raise CommandError(f"Refusing a symlink in public assets: {path}")
                relative = path.relative_to(source)
                if (path.is_file() and path.suffix.lower() in ASSET_EXTENSIONS
                        and not any(part.startswith(".") for part in relative.parts)):
                    destination = stage / "static" / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(path, destination)

    @classmethod
    def validate_references(cls, stage):
        for document in stage.glob("*.html"):
            parser = AssetReferences()
            parser.feed(document.read_text(encoding="utf-8"))
            for url in parser.urls:
                cls.validate_url(stage, document, url)
        for stylesheet in stage.rglob("*.css"):
            for url in CSS_URL.findall(stylesheet.read_text(encoding="utf-8")):
                cls.validate_url(stage, stylesheet, url.strip())
        cls.validate_url(stage, stage / "index.html", "/static/base/images/favicon.svg")

    @staticmethod
    def validate_url(stage, document, url):
        parsed = urlsplit(url)
        if parsed.scheme or parsed.netloc or not parsed.path:
            return
        base = "/" + document.relative_to(stage).as_posix()
        relative = unquote(urlsplit(urljoin(base, url)).path).lstrip("/")
        target = (stage / (relative or "index.html")).resolve()
        if not target.is_relative_to(stage.resolve()) or not target.is_file():
            raise CommandError(f"Missing or invalid public asset/link in {document.name}: {url}")

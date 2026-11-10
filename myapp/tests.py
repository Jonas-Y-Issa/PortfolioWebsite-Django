import importlib.util
import os
from importlib import import_module
from pathlib import Path
from unittest.mock import patch

from decouple import Config, RepositoryEmpty
from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles import finders
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.forms import modelform_factory
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from MyWebsite.middleware import TrustedProxyHeadersMiddleware
from myapp.models import About, Project, ProjectImage


class ProjectLinkSecurityTests(TestCase):
    def create_project(self, url):
        return Project.objects.create(
            inc=1, preface="Test", title="<script>alert('title')</script>",
            extLink=url, description="<script>alert('description')</script>", image="",
        )

    def test_unsafe_links_from_imports_are_not_rendered(self):
        for url in ["javascript:alert(1)", "data:text/html,<script>alert(1)</script>",
                    "//example.com", "ftp://example.com", "https://example.com\n"]:
            with self.subTest(url=url):
                project = self.create_project(url)
                self.assertEqual(project.public_url, "")
                response = self.client.get(reverse("index"))
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, 'class="project-link"')
                project.delete()

    def test_http_links_keep_their_url_and_text_is_escaped(self):
        for url in ["https://example.com/project?a=1&b=2", "http://example.com/project"]:
            with self.subTest(url=url):
                project = self.create_project(url)
                self.assertEqual(project.public_url, url)
                response = self.client.get(reverse("index"))
                self.assertContains(response, 'class="project-link"')
                self.assertContains(response, "&lt;script&gt;alert(&#x27;title&#x27;)&lt;/script&gt;")
                self.assertNotContains(response, "<script>alert(")
                project.delete()

    def test_admin_rejects_non_http_project_links(self):
        field = Project._meta.get_field("extLink")
        for url in ["javascript:alert(1)", "ftp://example.com"]:
            with self.subTest(url=url), self.assertRaises(ValidationError):
                field.clean(url, Project())

    def test_about_content_is_escaped(self):
        About.objects.create(description="<script>alert(1)</script>", image="", image_desc="Test")
        response = self.client.get(reverse("index"))
        self.assertContains(response, "&lt;script&gt;alert(1)&lt;/script&gt;")
        self.assertNotContains(response, "<script>alert(1)</script>")


class ProjectGalleryTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            inc=1,
            preface="Test",
            title="Chess",
            extLink="https://example.com/chess",
            description="A chess game.",
            image="legacy-cover.png",
        )

    def test_homepage_gallery_is_ordered_and_prefetched(self):
        for image, position in [("last.png", 2), ("first.png", 0), ("second.png", 0)]:
            ProjectImage.objects.create(
                project=self.project, image=image, caption=image, position=position,
            )
        other = Project.objects.create(
            inc=2, preface="Test", title="Other", extLink="https://example.com/other",
            description="Another project.", image="other.png",
        )
        ProjectImage.objects.create(project=other, image="other.png", caption="Other")

        response = self.client.get(reverse("index"))

        self.assertEqual(response.status_code, 200)
        with self.assertNumQueries(0):
            galleries = [
                [screenshot.image for screenshot in project.gallery.all()]
                for project in response.context["projects"]
            ]
        self.assertEqual(galleries, [["first.png", "second.png", "last.png"], ["other.png"]])

    def test_gallery_captions_are_escaped(self):
        ProjectImage.objects.create(
            project=self.project,
            image="gallery.png",
            caption='<script>alert("gallery")</script>',
        )

        response = self.client.get(reverse("index"))

        self.assertContains(response, "homepage/images/gallery.png")
        self.assertContains(response, "&lt;script&gt;alert(&quot;gallery&quot;)&lt;/script&gt;")
        self.assertNotContains(response, '<script>alert("gallery")</script>')
        self.assertNotContains(response, "homepage/images/legacy-cover.png")

    def test_project_without_gallery_keeps_its_cover(self):
        response = self.client.get(reverse("index"))
        self.assertContains(response, "homepage/images/legacy-cover.png")


class PortfolioContentMigrationTests(TestCase):
    def setUp(self):
        self.migration = import_module("myapp.migrations.0011_refresh_portfolio_projects")
        self.apps = MigrationExecutor(connection).loader.project_state(
            ("myapp", "0010_projectimage")
        ).apps
        self.Project = self.apps.get_model("myapp", "Project")
        self.ProjectImage = self.apps.get_model("myapp", "ProjectImage")

    def create_project(self, **fields):
        values = {
            "inc": 1,
            "preface": "Test",
            "title": "A project",
            "extLink": "https://example.com/project",
            "description": "Keep this original content.",
            "image": "original.png",
        }
        return self.Project.objects.create(**(values | fields))

    def apply_content_migration(self):
        self.migration.refresh_projects(self.apps, connection.schema_editor())

    def test_chess_gallery_is_seeded_once_and_existing_content_is_preserved(self):
        chess = self.create_project(extLink=f"{self.migration.CHESS_URL.upper()}/")
        existing = self.ProjectImage.objects.create(
            project=chess, image="custom.png", caption="Keep this screenshot", position=10,
        )
        unrelated = self.create_project(extLink="https://example.com/unrelated")
        original = self.Project.objects.filter(pk=unrelated.pk).values().get()

        self.apply_content_migration()
        self.apply_content_migration()

        chess.refresh_from_db()
        self.assertEqual(str(chess.image), "chess-gameplay.png")
        self.assertEqual(chess.description, "Keep this original content.")
        self.assertEqual(
            list(chess.gallery.values_list("image", "caption", "position")),
            [
                ("chess-gameplay.png", "Four-player chess in progress", 0),
                ("chess-menu.png", "Main menu", 1),
                ("chess-colour-selection.png", "Player colour selection", 2),
                ("chess-results.png", "Match results", 3),
                ("custom.png", "Keep this screenshot", 10),
            ],
        )
        self.assertTrue(self.ProjectImage.objects.filter(pk=existing.pk).exists())
        self.assertEqual(self.Project.objects.filter(pk=unrelated.pk).values().get(), original)

    def test_only_the_identified_pi_portfolio_is_deleted(self):
        pi_fields = {
            "title": "Portfolio Website Github",
            "image": "pi.jpeg",
            "extLink": f"{self.migration.OLD_PORTFOLIO_URL.upper()}/",
        }
        obsolete = self.create_project(**pi_fields)
        preserved = [
            self.create_project(**(pi_fields | {"title": "Another portfolio"})),
            self.create_project(**(pi_fields | {"image": "another.png"})),
            self.create_project(**(pi_fields | {"extLink": "https://example.com/unrelated"})),
        ]
        original = list(self.Project.objects.exclude(pk=obsolete.pk).order_by("pk").values())

        self.apply_content_migration()

        self.assertFalse(self.Project.objects.filter(pk=obsolete.pk).exists())
        self.assertEqual(list(self.Project.objects.order_by("pk").values()), original)
        self.assertEqual(self.Project.objects.count(), len(preserved))

    def test_empty_database_is_left_empty(self):
        self.apply_content_migration()
        self.assertFalse(self.Project.objects.exists())
        self.assertFalse(self.ProjectImage.objects.exists())


class ChessResultsRemovalMigrationTests(TestCase):
    def setUp(self):
        self.migration = import_module("myapp.migrations.0013_remove_chess_results")
        self.apps = MigrationExecutor(connection).loader.project_state(
            ("myapp", "0012_remove_chess_colour_selection")
        ).apps
        self.Project = self.apps.get_model("myapp", "Project")
        self.ProjectImage = self.apps.get_model("myapp", "ProjectImage")

    def test_only_chess_results_are_removed_and_repeating_is_safe(self):
        chess_urls = [
            "https://github.com/Jonas-Y-Issa/4-Way-Chess",
            "https://github.com/Jonas-Y-Issa/4-Way-Chess/".upper(),
        ]
        removed_ids = []
        for url in chess_urls + ["https://example.com/another-project"]:
            project = self.Project.objects.create(
                inc=1, preface="Test", title="Chess", extLink=url,
                description="Keep the project.", image="chess-gameplay.png",
            )
            for image, position in [
                ("chess-gameplay.png", 0),
                ("chess-menu.png", 1),
                ("chess-results.png", 3),
                ("custom.png", 3),
            ]:
                screenshot = self.ProjectImage.objects.create(
                    project=project, image=image, caption=image, position=position,
                )
                if url in chess_urls and image == "chess-results.png":
                    removed_ids.append(screenshot.pk)
        original_projects = list(self.Project.objects.order_by("pk").values())
        preserved_images = list(
            self.ProjectImage.objects.exclude(pk__in=removed_ids).order_by("pk").values()
        )

        for _ in range(2):
            self.migration.remove_chess_results(self.apps, connection.schema_editor())

        self.assertFalse(self.ProjectImage.objects.filter(pk__in=removed_ids).exists())
        self.assertEqual(list(self.ProjectImage.objects.order_by("pk").values()), preserved_images)
        self.assertEqual(list(self.Project.objects.order_by("pk").values()), original_projects)

    def test_empty_database_is_left_empty(self):
        self.migration.remove_chess_results(self.apps, connection.schema_editor())
        self.assertFalse(self.Project.objects.exists())
        self.assertFalse(self.ProjectImage.objects.exists())


class AboutPortraitRemovalTests(TestCase):
    def setUp(self):
        self.migration = import_module("myapp.migrations.0014_remove_about_portrait")
        self.apps = MigrationExecutor(connection).loader.project_state(
            ("myapp", "0013_remove_chess_results")
        ).apps
        self.About = self.apps.get_model("myapp", "About")

    def test_only_retired_portrait_content_is_cleared_and_repeating_is_safe(self):
        retired = self.About.objects.create(
            description="Keep my biography.", image="profile.jpeg",
            image_desc=self.migration.RETIRED_CAPTION,
        )
        custom_caption = self.About.objects.create(
            description="Keep this biography too.", image="profile.jpeg",
            image_desc="A separately edited caption.",
        )
        unrelated = self.About.objects.create(
            description="Another biography.", image="other.jpeg",
            image_desc=self.migration.RETIRED_CAPTION,
        )
        original_unrelated = self.About.objects.filter(pk=unrelated.pk).values().get()

        for _ in range(2):
            self.migration.remove_about_portrait(self.apps, connection.schema_editor())

        retired.refresh_from_db()
        custom_caption.refresh_from_db()
        self.assertEqual(str(retired.image), "")
        self.assertEqual(retired.image_desc, "")
        self.assertEqual(retired.description, "Keep my biography.")
        self.assertEqual(str(custom_caption.image), "")
        self.assertEqual(custom_caption.image_desc, "A separately edited caption.")
        self.assertEqual(custom_caption.description, "Keep this biography too.")
        self.assertEqual(self.About.objects.filter(pk=unrelated.pk).values().get(), original_unrelated)
        self.assertEqual(self.About.objects.count(), 3)

    def test_empty_database_is_left_empty(self):
        self.migration.remove_about_portrait(self.apps, connection.schema_editor())
        self.assertFalse(self.About.objects.exists())

    def test_about_form_can_save_a_biography_without_an_image_or_caption(self):
        AboutForm = modelform_factory(About, fields=("description", "image", "image_desc"))
        form = AboutForm(data={"description": "A biography without a photograph."})

        self.assertTrue(form.is_valid(), form.errors)
        about = form.save()
        about.refresh_from_db()
        self.assertEqual(about.description, "A biography without a photograph.")
        self.assertEqual(str(about.image), "")
        self.assertEqual(about.image_desc, "")


class ProductionSettingsTests(SimpleTestCase):
    def load_settings(self, **environment):
        path = Path(settings.BASE_DIR) / "MyWebsite/settings.py"
        spec = importlib.util.spec_from_file_location("isolated_settings", path)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(os.environ, environment, clear=True), patch("decouple.config", Config(RepositoryEmpty())):
            spec.loader.exec_module(module)
        return module

    def production_environment(self):
        from django.core.management.utils import get_random_secret_key
        return {"DEBUG": "False", "SECRET_KEY": get_random_secret_key(),
                "DJANGO_ALLOWED_HOSTS": "portfolio.example.com"}

    def test_production_requires_secret_and_hosts(self):
        with self.assertRaises(ImproperlyConfigured):
            self.load_settings(DEBUG="False")
        for hosts in ["", "*"]:
            environment = self.production_environment() | {"DJANGO_ALLOWED_HOSTS": hosts}
            with self.subTest(hosts=hosts), self.assertRaises(ImproperlyConfigured):
                self.load_settings(**environment)

    def test_repeated_secret_is_rejected(self):
        environment = self.production_environment() | {"SECRET_KEY": "x" * 60}
        with self.assertRaises(ImproperlyConfigured):
            self.load_settings(**environment)

    def test_false_is_false_and_cookies_are_secure(self):
        for false_value in ["False", "0"]:
            module = self.load_settings(**(self.production_environment() | {"DEBUG": false_value}))
            self.assertFalse(module.DEBUG)
            self.assertTrue(module.SECURE_SSL_REDIRECT)
            self.assertTrue(module.SESSION_COOKIE_SECURE)
            self.assertTrue(module.CSRF_COOKIE_SECURE)

    def test_proxy_requires_exact_trusted_peer_addresses(self):
        environment = self.production_environment() | {"DJANGO_TRUST_PROXY": "True"}
        for peers in ["", "*", "0.0.0.0/0"]:
            with self.subTest(peers=peers), self.assertRaises(ImproperlyConfigured):
                self.load_settings(**(environment | {"DJANGO_TRUSTED_PROXY_IPS": peers}))
        module = self.load_settings(**(environment | {"DJANGO_TRUSTED_PROXY_IPS": "172.30.75.2 127.0.0.1 ::1"}))
        self.assertEqual(module.SECURE_PROXY_SSL_HEADER, ("HTTP_X_FORWARDED_PROTO", "https"))


@override_settings(DJANGO_TRUSTED_PROXY_IPS=["172.30.75.2", "127.0.0.1"],
                   SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO", "https"))
class TrustedProxyTests(SimpleTestCase):
    def request_through_middleware(self, peer):
        request = RequestFactory().get("/", REMOTE_ADDR=peer, HTTP_X_FORWARDED_PROTO="https")
        middleware = TrustedProxyHeadersMiddleware(lambda request: HttpResponse(str(request.is_secure())))
        return middleware(request)

    def test_untrusted_peer_cannot_spoof_https(self):
        for peer in ["172.30.75.3", "198.51.100.8", "", "invalid"]:
            with self.subTest(peer=peer):
                self.assertEqual(self.request_through_middleware(peer).content, b"False")

    def test_gateway_and_healthcheck_headers_work(self):
        for peer in ["172.30.75.2", "127.0.0.1"]:
            with self.subTest(peer=peer):
                self.assertEqual(self.request_through_middleware(peer).content, b"True")


class StaticSupplyChainTests(SimpleTestCase):
    def test_admin_assets_come_from_installed_django(self):
        admin_directory = Path(admin.__file__).resolve().parent
        for name in ["admin/js/core.js", "admin/js/vendor/jquery/jquery.js",
                     "admin/js/vendor/select2/select2.full.min.js"]:
            with self.subTest(asset=name):
                path = Path(finders.find(name)).resolve()
                self.assertTrue(path.is_relative_to(admin_directory))

    def test_templates_do_not_load_compromised_cdn(self):
        for template in (Path(settings.BASE_DIR) / "templates").rglob("*.html"):
            with self.subTest(template=template.name):
                self.assertNotIn("polyfill.io", template.read_text())

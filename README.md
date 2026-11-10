# Portfolio website

Jonas Issa's terminal-inspired portfolio, built with Django, SQLite, and plain HTML, CSS, and JavaScript. Production uses Gunicorn and WhiteNoise behind the portfolio's Nginx gateway.

The homepage is served at `/` and administration at `/admin/`. The former `/Django/` route and framework selection page have been removed.

## Local development

The project uses Django 5.2 LTS. Activate your existing Python virtual environment and refresh its dependencies after updating:

```sh
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open <http://127.0.0.1:8000/>. Local development defaults to `DEBUG=True` and localhost hosts. Production requires a private `SECRET_KEY` and explicit hostname settings.

## Project layout

- `MyWebsite/`: settings, routes, proxy middleware, and server entry points.
- `myapp/`: portfolio models, views, admin registration, tests, migrations, and fixtures.
- `templates/`: the shared `base.html`, homepage `Index.html`, and error page.
- `myapp/static/base/`: shared styles, fonts, favicon, and `portfolio.js` interactions.
- `myapp/static/homepage/`: section styles and portfolio images.
- `experiments/`: the archived physics template and stylesheet. These drafts have no routes and are excluded from template discovery, static collection, and the production image.

`MyWebsite/settings.py` is the single maintained configuration. The small top-level `settings.py`, `urls.py`, `wsgi.py`, and `asgi.py` modules delegate to it for older deployment commands. Database migrations retain their original app and model names.

## Editing the design

Edit source files under `myapp/static/`. Stylesheet names use lowercase words separated by hyphens:

- `base/css/variables.css` defines fonts and default colors; `base/css/theme.css` defines the light theme.
- `base/css/` also contains shared layout, header, footer, and scrolling styles.
- `homepage/css/` contains the introduction, word cube, projects, project tabs, about, and skills styles.

`templates/base.html` and `templates/Index.html` load their styles explicitly. `base/scripts/portfolio.js` handles theme switching, navigation, typewriter motion, and project tabs.

`staticfiles/` is ignored, generated deployment output. Django's development server serves the source assets directly. Regenerate deployment assets with `python manage.py collectstatic --clear --noinput`; `--clear` removes old filenames after renaming or deleting source assets.

## Portfolio content

Projects, about text, and skills remain editable through Django admin. Project and about image filenames refer to files in `myapp/static/homepage/images/`. Keep these images when cleaning assets; their references live in the database.

The toolkit uses the `Skills` records in the database. `myapp/fixtures/toolkit.json` contains six curated groups: languages, web/APIs, apps/games, data/AI, infrastructure, and testing/automation.

To apply this snapshot to another database, run `python manage.py loaddata toolkit`. It updates toolkit records 1–6; it does not change project or about content. The site does not scan your local project folders at runtime. The older `Apps` model remains available in admin to preserve existing data.

## Checks

```sh
DEBUG=True python manage.py test myapp
python manage.py check
python manage.py makemigrations --check --dry-run
```

Tests use an isolated database and cover production settings, proxy spoofing, project URLs, escaped content, and static assets. If `pip-audit` is installed, run `python -m pip_audit -r requirements.txt` to audit dependencies.

## Production deployment

Use the parent repository's [GitHub → Raspberry Pi → Cloudflare Tunnel guide](../DevOps/production/README.md). It uses persistent SQLite volumes, production settings, and GitHub-built ARM64 images. The maintained Dockerfile and startup script live under `../DevOps/production/django/`.

Production rejects missing or weak secrets, wildcard hosts, and proxy trust without explicit peer IPs. Set `DJANGO_TRUST_PROXY=True` only behind the private deployment gateway, with `DJANGO_TRUSTED_PROXY_IPS` containing the gateway's exact IP and any local healthcheck IPs. The production Compose file provides these values; its gateway overwrites forwarded headers. Application ports stay private.

Keep real `.env` files and SQLite databases out of Git. Rotate any previously committed secrets; deleting them from the current files does not remove old Git history or invalidate credentials. Django admin assets come from the installed Django package; copied assets in `myapp/static/admin/` would hide future framework fixes.

Run `python manage.py check --deploy` with the production environment before publishing. HSTS deliberately covers only this hostname; enable subdomain HSTS or preload only when all affected hostnames support permanent HTTPS.

Live site: <https://developerjonas.com/>.

# Portfolio website

Jonas Issa's terminal-inspired portfolio, built with Django, SQLite, and plain HTML, CSS, and JavaScript. Django provides local content editing; the public site can be exported to static files for Cloudflare Pages.

The homepage is served at `/`. Administration is available at `/admin/` when running Django locally; it is not part of the static site. The former `/Django/` route and framework selection page have been removed.

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
- `myapp/management/commands/export_pages.py`: generates the Cloudflare Pages upload from local content.
- `templates/`: the shared `base.html`, homepage `Index.html`, and error page.
- `myapp/static/base/`: shared styles, fonts, favicon, and `portfolio.js` interactions.
- `myapp/static/homepage/`: section styles and portfolio images.

`MyWebsite/settings.py` is the single maintained configuration. The small top-level `settings.py`, `urls.py`, `wsgi.py`, and `asgi.py` modules delegate to it for older deployment commands. Database migrations retain their original app and model names.

## Editing the design

Edit source files under `myapp/static/`. Stylesheet names use lowercase words separated by hyphens:

- `base/css/variables.css` defines fonts and default colors; `base/css/theme.css` defines the light theme.
- `base/css/` also contains shared layout, header, footer, and scrolling styles.
- `homepage/css/` contains the introduction, word cube, projects, project tabs, about, and skills styles.

`templates/base.html` and `templates/Index.html` load their styles explicitly. `base/scripts/portfolio.js` handles theme switching, navigation, typewriter motion, and project tabs.

`staticfiles/` is ignored, generated output for server-based Django deployments. Django's development server serves the source assets directly. Cloudflare Pages uses `export_pages` instead of `collectstatic`; the exporter reads the source assets directly.

## Portfolio content

Projects, about text, and skills remain editable through Django admin. Project and about image filenames refer to files in `myapp/static/homepage/images/`. Keep these images when cleaning assets; their references live in the database.

About photos and captions are optional. Entries without a photo display the about text without an empty image column.

Projects can also have a screenshot slideshow. Add gallery rows on the project's admin page with an image filename, caption, and position. Multiple images cycle every five seconds with previous/next, play/pause, thumbnails, keyboard controls, and touch swiping. Cycling pauses while hovered or out of view, and stops on manual navigation, keyboard focus, or a reduced-motion preference. Projects without gallery rows use their existing cover image. Add image files to `myapp/static/homepage/images/`, then export and upload again for Pages. Files placed only in `staticfiles/` are generated output and can be cleared during deployment.

Migrations `0010` and `0011` add gallery support, attach the chess screenshots, and remove the retired Pi-hosting project. Migrations `0012` and `0013` remove the colour-selection and match-results screenshots, leaving gameplay and the main menu. Migration `0014` removes the retired Felsensteg/Birg portrait while preserving the about text. These content updates match existing records and do not create sample content in an empty database. Back up an existing database before applying content migrations; their content changes are irreversible through Django migrations.

The toolkit uses the `Skills` records in the database. `myapp/fixtures/toolkit.json` contains six curated groups: languages, web/APIs, apps/games, data/AI, infrastructure, and testing/automation.

To apply this snapshot to another database, run `python manage.py loaddata toolkit`. It updates toolkit records 1–6; it does not change project or about content. The site does not scan your local project folders at runtime. The older `Apps` model remains available in admin to preserve existing data.

## Checks

```sh
DEBUG=True python manage.py test myapp
python manage.py check
python manage.py makemigrations --check --dry-run
```

Tests use an isolated database and cover production settings, proxy spoofing, project URLs, escaped content, static assets, and safe Pages export. If `pip-audit` is installed, run `python -m pip_audit -r requirements.txt` to audit dependencies.

## Cloudflare Pages deployment

Pages serves the generated HTML, styles, scripts, fonts, and images. The slideshow, project tabs, expandable stories, and theme switch work without a Django server. Content changes become public when you export and upload a new version.

### Build the upload

Use the local database containing your portfolio content, with migrations already applied:

```sh
DEBUG=True python -B manage.py export_pages
```

This creates both `build/pages/` and `build/pages.zip`. The ZIP has `index.html` at its root, ready for dashboard upload. The build includes a custom `404.html`, so unavailable routes such as `/admin/` return a not-found page. It excludes the database, environment files, backups, Django admin assets, and application source. Both outputs are ignored by Git.

The command replaces its previous generated output only after rendering and checking the new site. Fix missing image filenames in the local admin or restore the source image before exporting again. Keep your local SQLite database backed up: it remains the editable source of your content.

To preview the generated homepage:

```sh
python -B -m http.server 8080 --bind 127.0.0.1 --directory build/pages
```

Open <http://127.0.0.1:8080/>. This simple preview server does not apply Cloudflare's redirects or custom error-page routing; view `/404.html` directly to preview that page.

### First upload and domain

1. In the [Cloudflare dashboard](https://dash.cloudflare.com/), open **Workers & Pages → Create application** and choose the **Pages / Drag and drop** flow.
2. Name the project `developerjonas-portfolio` (or choose another available name), upload **`build/pages.zip`**, and deploy. Upload the generated ZIP or `build/pages` folder, rather than the project checkout.
3. Open the `pages.dev` address Cloudflare gives you and check the homepage.
4. In that Pages project, open **Custom domains → Set up a domain**, enter **`developerjonas.com`**, and follow the DNS confirmation. Add `www.developerjonas.com` here too if you want it to work.
5. Wait until Cloudflare shows the domain as active, then check it over HTTPS. If the hostname still points to an old server or tunnel, update that hostname's record through the Pages setup; leave unrelated DNS records in place.

Use the Pages custom-domain flow before changing DNS manually. See Cloudflare's [Direct Upload guide](https://developers.cloudflare.com/pages/get-started/direct-upload/) and [custom-domain guide](https://developers.cloudflare.com/pages/configuration/custom-domains/).

This project uses Direct Upload because its content lives in your local database. Connecting the source repository alone would not give Cloudflare that content. A Direct Upload project cannot be switched to Git integration in place, but uploads can later be automated with Wrangler or CI.

### Publish later changes

Edit content in local Django admin, or edit templates and source assets, then run `export_pages` again. In your Pages project, choose **Create a new deployment**, select **Production**, and upload the new `build/pages.zip`.

Optional terminal deployment with Node.js and Cloudflare's Wrangler CLI:

```sh
npx wrangler@4 login
npx wrangler@4 pages project list
npx wrangler@4 pages deploy build/pages --project-name=developerjonas-portfolio --branch=main
```

Use the project name and production branch configured in your Cloudflare project; `main` above is an example. Wrangler uploads the folder, not the ZIP. For a project created entirely through the CLI, create it once with `npx wrangler@4 pages project create developerjonas-portfolio --production-branch=main` before deploying.

## Optional Django server deployment

The parent repository's [deployment guide](../DevOps/production/README.md) retains the server-based Docker setup using Gunicorn, WhiteNoise, and persistent SQLite volumes. It is not needed for Pages. Server deployments require production secrets, explicit hostnames and trusted proxy IPs, `collectstatic`, and `python manage.py check --deploy`.

Keep real `.env` files and SQLite databases out of Git and uploads. Django admin assets come from the installed Django package; copied assets in `myapp/static/admin/` would hide future framework fixes.

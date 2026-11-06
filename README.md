# A Terminal Inspired Portfolio Website

## Stack

Python/Django/Gunicorn/Nginx/MariaDB/Javascript/Docker/Terraform/Azure

Currently Running @ <https://developerjonas.com/Django>

![ksnip_20230119-150824](https://user-images.githubusercontent.com/110714003/213353015-9f0cab28-845e-4e02-9ce1-3397e5c52c7b.png)

## Editing the design

Edit the source stylesheets in these folders:

- `myapp/static/base/css/`: shared styles, header, intro, sections, and footer. Change fonts and default colors in `Variables.css`, and light-theme colors in `Dark-mode.css`.
- `myapp/static/homepage/css/`: projects, slideshow controls, about, skills, and the rotating word cube (`3dCube.css`).
- `rootPage/static/root/css/root.css`: the framework selection page.

`templates/base.html` loads the shared styles. `templates/Index.html` and `templates/root.html` load their page-specific styles in the `head` block.

`staticfiles/` contains generated deployment copies. Make changes in the source folders above; Django's development server serves them directly. Regenerate deployment assets with `python manage.py collectstatic --noinput`.

## Toolkit content

The toolkit uses the `Skills` records in the database and remains editable through Django admin. `myapp/fixtures/toolkit.json` contains the six groups curated from the local project collection: languages, web/APIs, apps/games, data/AI, infrastructure, and testing/automation.

To apply this snapshot to another database, run `python manage.py loaddata toolkit`. It updates toolkit records 1–6; it does not change project or about content. The site does not scan your local project folders at runtime.

## For CI/CD Pipeline Please see Parent Repo

## Setup

### Required for Options

#### - Startup Docker Registry

```Shell
# Start Docker Registry
    docker run -d -p 5000:5000 --restart always --name registry registry:2
```

### Recommended

#### - Install
Docker, Sqlite3, dotnet cli, dotnet ef
#### - General Tips

For faster development it is recommended to setup these commands into a build script, this can be done in azure or even something as simple as tasks.json if youre using VS Code.  
An example of tasks.json for this project can be found in the parent repo which contains all things CI/CD.

#### - Portainer for RaspberryPi

```Shell
# Pull Latest Portainer
    docker pull portainer/portainer-ce:latest
# Run Portainer and set restart flag to always
    docker run -d -p 9000:9000 --name portainer --restart always -v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:/data portainer/portainer-ce:latest
```

```Portainer Url - http://raspberrypi-hostname:9000```

## Option 0: - Run as Service

```Shell
# Secure Copy Build to Pi
    scp Django-Portfolio [user]@[website.com]:~/
```

### RaspberryPi

You will need to setup GUnicorn to run the service as a socket in NGinx

Create a Service file on your Pi and run it using  

```Shell
#systemd service
    sudo systemctl start DjangoPortfolio.service
```

## Option 1: - Manual Docker Deploy

### Build Image

```Shell
# Build Production 
    dotnet publish -c Release --runtime linux-arm64

# Build Image for linux/arm64 using buildx
    #--file [path to Dockerfile]
    #--platform [os]/[architecture]
    docker buildx build --file DevOps/Docker/Dockerfile --load --platform linux/arm64 -t django-portfolio-image:latest .

# Test using inspect
    #-should return "linux/arm64"
    docker image inspect django-portfolio-image:latest -f '{{.Os}}/{{.Architecture}}'

# Export Image as tar file
    docker save -o DevOps/Docker/images/django-portfolio-image.tar django-portfolio-image:latest

    docker tag django-portfolio-image:latest localhost:5000/django-portfolio-image

# Using Portainer
    docker push localhost:5000/django-portfolio-image:latest

# Not Using Portainer
    # - Secure Copy image to Pi
    scp DevOps/Docker/django-portfolio-image.tar [user]@[website.com]:~/

```

## Option 2: - CI/CD Docker Deploy Setup

### Automated

#### Build Docker Images

```Shell
# Build docker Images through Docker Compose
    docker compose -f ${workspaceFolder}/DevOps/Docker/docker-compose.build.yml build --no-cache
```

#### Docker Swarm

```Shell
# Initialise
    docker swarm init
    docker stack deploy -c DevOps/Docker/docker-compose.yml
    docker tag django-portfolio-image localhost:5000/django-portfolio-image:latest

# Push Image to registry
    docker push localhost:5000/django-portfolio-image:latest

# Export Image as tar file
    docker save -o DevOps/Docker/images/django-portfolio-image.tar django-portfolio-image:latest

    docker tag django-portfolio-image:latest localhost:5000/django-portfolio-image
```

```Shell
# Stop and Remove Registry
    docker container stop registry
    docker container rm -v registry
```

## How to Test Image

### Enter Image and check directory

```Shell
# Check Running Stats
    docker stats
# Run Image in a container in Interactive mode
    docker run -it --rm django-portfolio-image:latest django-portfolio-container
    docker exec -it django-portfolio-container sh
```

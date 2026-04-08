# Deployment Runbook

Stand: GitHub-Actions-Deploy mit Domain, nginx-Reverse-Proxy und Let's-Encrypt-fähigem HTTPS.

## Zielbild

- GitHub Actions deployt auf den Server `alveran`
- Zugriff erfolgt über eine Domain oder Subdomain
- die Oberfläche ist per HTTP Basic Auth geschützt
- nginx läuft als Reverse Proxy auf Port 80/443 und leitet `/grafana/` an Grafana weiter
- der Observability-Stack läuft intern (Prometheus, Tempo, Loki, Alloy, Grafana)
- `/health` bleibt ohne Auth erreichbar, damit Docker-Healthchecks funktionieren
- FastAPI-Dokumentation ist im Produktionsmodus standardmäßig deaktiviert

## Voraussetzungen

- Docker Engine + Compose Plugin sind auf dem Server installiert
- der Server ist per SSH erreichbar: `ssh alveran`
- Port `80/tcp` und `443/tcp` sind in der Firewall offen
- `APP_DOMAIN` zeigt per DNS auf die Server-IP
- ein Zielverzeichnis existiert, z. B. `/opt/namenschmiede`

## GitHub-Secrets

Für den Deploy-Workflow werden folgende Repository-Secrets benötigt:

- `DEPLOY_HOST` – Server-IP oder SSH-Host
- `DEPLOY_PORT` – optional, Standard `22`
- `DEPLOY_USER` – SSH-User für das Deployment
- `DEPLOY_SSH_KEY` – privater SSH-Key für GitHub Actions
- `GHCR_USERNAME` – Benutzername für GHCR
- `GHCR_TOKEN` – Token mit `read:packages`
- `APP_DOMAIN` – öffentliche Domain oder Subdomain der Web-App
- `APP_BASIC_AUTH_USERNAME` – Loginname für die Web-App
- `APP_BASIC_AUTH_PASSWORD` – Passwort für die Web-App
- `GRAFANA_ADMIN_USER` – optional, Standard `admin`
- `GRAFANA_ADMIN_PASSWORD` – Passwort für Grafana
- `DEPLOY_TARGET_DIR` – optional, Standard `/opt/namenschmiede`

## Erst-Setup auf dem Server

```bash
ssh alveran
mkdir -p /opt/namenschmiede/infra
mkdir -p /opt/namenschmiede/certbot/conf
mkdir -p /opt/namenschmiede/certbot/www
cd /opt/namenschmiede
cp infra/.env.example infra/.env
```

## Erforderliche Konfiguration

Datei: `infra/.env`

```env
IMAGE_NAME=ghcr.io/cmdhertel/aventurische-namensschmiede/namegen-web
IMAGE_TAG=latest
APP_DOMAIN=namen.example.de
APP_BASIC_AUTH_USERNAME=admin
APP_BASIC_AUTH_PASSWORD=<starkes-passwort>
APP_ENABLE_API_DOCS=0
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=<starkes-passwort>
```

Die Datei wird im Normalfall vom Deploy-Workflow bei jedem Rollout neu geschrieben.

## Initiale Zertifikatsausstellung

Beim ersten Start existiert noch kein Zertifikat. nginx startet deshalb zunächst mit HTTP und stellt gleichzeitig das ACME-Webroot unter `/.well-known/acme-challenge/` bereit.

1. DNS prüfen:

```bash
dig +short namen.example.de
```

2. Stack einmal starten:

```bash
cd /opt/namenschmiede
docker compose --env-file infra/.env -f infra/docker-compose.prod.yml up -d
```

3. Zertifikat holen:

```bash
docker run --rm \
  -v /opt/namenschmiede/certbot/conf:/etc/letsencrypt \
  -v /opt/namenschmiede/certbot/www:/var/www/certbot \
  certbot/certbot certonly \
  --webroot -w /var/www/certbot \
  -d namen.example.de \
  --email <deine-mail> \
  --agree-tos \
  --no-eff-email
```

4. nginx mit Zertifikat neu starten:

```bash
cd /opt/namenschmiede
docker compose --env-file infra/.env -f infra/docker-compose.prod.yml restart nginx
```

## Deploy-Fluss

1. Push nach `main`
2. GitHub Actions baut und pusht `namegen-web` nach GHCR
3. Der Deploy-Job kopiert `infra/docker-compose.prod.yml`, `ops/observability/*`
   und `ops/nginx/*` als Bundle auf den Server
4. Der Deploy-Job schreibt `infra/.env` mit `IMAGE_TAG=<git-sha>` sowie Domain-,
   Auth- und Grafana-Credentials
5. Der Server zieht das neue Image und startet den kompletten Stack via
   `docker compose up -d`

## Manuelles Rollback

Auf dem Server:

```bash
cd /opt/namenschmiede
sed -i 's/^IMAGE_TAG=.*/IMAGE_TAG=<alte-sha>/' infra/.env
docker compose --env-file infra/.env -f infra/docker-compose.prod.yml pull
docker compose --env-file infra/.env -f infra/docker-compose.prod.yml up -d
```

## Prüfung

- Healthcheck ohne Auth:
  - `curl https://<DOMAIN>/health`
- Web-App mit Auth:
  - `curl -u admin:<passwort> https://<DOMAIN>/`
- Grafana:
  - `https://<DOMAIN>/grafana/`
- API-Dokumentation bei Bedarf temporär aktivieren:
  - `APP_ENABLE_API_DOCS=1`
- HTTP-Redirect prüfen:
  - `curl -I http://<DOMAIN>/`

## Zertifikat erneuern

Regelmäßig ausführen, z. B. per Cron oder systemd timer:

```bash
docker run --rm \
  -v /opt/namenschmiede/certbot/conf:/etc/letsencrypt \
  -v /opt/namenschmiede/certbot/www:/var/www/certbot \
  certbot/certbot renew
```

Danach nginx reloaden:

```bash
cd /opt/namenschmiede
docker compose --env-file infra/.env -f infra/docker-compose.prod.yml exec nginx nginx -s reload
```

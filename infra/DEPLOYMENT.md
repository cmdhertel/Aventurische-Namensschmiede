# Deployment Runbook

Stand: GitHub-Actions-Deploy auf einen Server ohne DNS und ohne TLS-Termination.

## Zielbild

- GitHub Actions deployt auf den Server `alveran`
- Zugriff erfolgt vorerst direkt per Server-IP
- die Oberfläche ist per HTTP Basic Auth geschützt
- nginx läuft als Reverse Proxy auf Port 80 und leitet `/grafana/` an Grafana weiter
- der Observability-Stack läuft intern (Prometheus, Tempo, Loki, Alloy, Grafana)
- `/health` bleibt ohne Auth erreichbar, damit Docker-Healthchecks funktionieren
- FastAPI-Dokumentation ist im Produktionsmodus standardmäßig deaktiviert

## Voraussetzungen

- Docker Engine + Compose Plugin sind auf dem Server installiert
- der Server ist per SSH erreichbar: `ssh alveran`
- Port `80/tcp` ist in der Firewall offen
- ein Zielverzeichnis existiert, z. B. `/opt/namenschmiede`

## GitHub-Secrets

Für den Deploy-Workflow werden folgende Repository-Secrets benötigt:

- `DEPLOY_HOST` – Server-IP oder SSH-Host
- `DEPLOY_PORT` – optional, Standard `22`
- `DEPLOY_USER` – SSH-User für das Deployment
- `DEPLOY_SSH_KEY` – privater SSH-Key für GitHub Actions
- `GHCR_USERNAME` – Benutzername für GHCR
- `GHCR_TOKEN` – Token mit `read:packages`
- `APP_BASIC_AUTH_USERNAME` – Loginname für die Web-App
- `APP_BASIC_AUTH_PASSWORD` – Passwort für die Web-App
- `GRAFANA_ADMIN_USER` – optional, Standard `admin`
- `GRAFANA_ADMIN_PASSWORD` – Passwort für Grafana
- `DEPLOY_TARGET_DIR` – optional, Standard `/opt/namenschmiede`

## Erst-Setup auf dem Server

```bash
ssh alveran
mkdir -p /opt/namenschmiede/infra
cd /opt/namenschmiede
cp infra/.env.example infra/.env
```

## Erforderliche Konfiguration

Datei: `infra/.env`

```env
IMAGE_NAME=ghcr.io/cmdhertel/aventurische-namensschmiede/namegen-web
IMAGE_TAG=latest
APP_BASIC_AUTH_USERNAME=admin
APP_BASIC_AUTH_PASSWORD=<starkes-passwort>
APP_ENABLE_API_DOCS=0
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=<starkes-passwort>
```

Die Datei wird im Normalfall vom Deploy-Workflow bei jedem Rollout neu geschrieben.

## Deploy-Fluss

1. Push nach `main`
2. GitHub Actions baut und pusht `namegen-web` nach GHCR
3. Der Deploy-Job kopiert `infra/docker-compose.prod.yml`, `ops/observability/*`
   und `ops/nginx/*` als Bundle auf den Server
4. Der Deploy-Job schreibt `infra/.env` mit `IMAGE_TAG=<git-sha>` sowie den
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
  - `curl http://<SERVER-IP>/health`
- Web-App mit Auth:
  - `curl -u admin:<passwort> http://<SERVER-IP>/`
- Grafana:
  - `http://<SERVER-IP>/grafana/`
- API-Dokumentation bei Bedarf temporär aktivieren:
  - `APP_ENABLE_API_DOCS=1`

## Nächster Schritt nach DNS

Sobald eine Domain existiert, sollte der Stack um Reverse Proxy und TLS ergänzt werden:

- Traefik oder Caddy vor die App
- HTTPS via Let's Encrypt
- Security Headers und Rate Limiting auf Proxy-Ebene

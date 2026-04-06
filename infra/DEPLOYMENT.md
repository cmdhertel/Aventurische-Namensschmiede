# Deployment Runbook

Stand: IP-basierter Erst-Deploy ohne DNS und ohne TLS-Termination.

## Zielbild

- die Web-App läuft auf dem Server `alveran`
- Zugriff erfolgt vorerst direkt per Server-IP
- die Oberfläche ist per HTTP Basic Auth geschützt
- `/health` bleibt ohne Auth erreichbar, damit Docker-Healthchecks funktionieren

## Voraussetzungen

- Docker Engine + Compose Plugin sind auf dem Server installiert
- der Server ist per SSH erreichbar: `ssh alveran`
- Port `80/tcp` ist in der Firewall offen

## Erst-Setup auf dem Server

```bash
ssh alveran
git clone <repo-url>
cd Aventurische-Namensschmiede
cp infra/.env.example infra/.env
vim infra/.env
docker compose --env-file infra/.env -f infra/docker-compose.prod.yml up -d --build
```

## Erforderliche Konfiguration

Datei: `infra/.env`

```env
WEB_PORT=80
APP_BASIC_AUTH_USERNAME=admin
APP_BASIC_AUTH_PASSWORD=<starkes-passwort>
```

## Update

```bash
ssh alveran
cd Aventurische-Namensschmiede
git pull
docker compose --env-file infra/.env -f infra/docker-compose.prod.yml up -d --build
```

## Prüfung

- Healthcheck ohne Auth:
  - `curl http://<SERVER-IP>/health`
- Web-App mit Auth:
  - `curl -u admin:<passwort> http://<SERVER-IP>/`

## Nächster Schritt nach DNS

Sobald eine Domain existiert, sollte der Stack um Reverse Proxy und TLS ergänzt werden:

- Traefik oder Caddy vor die App
- HTTPS via Let's Encrypt
- Security Headers und Rate Limiting auf Proxy-Ebene


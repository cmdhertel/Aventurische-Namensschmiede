# VPS Setup Guide

Zielsystem: Ubuntu 24.04 LTS, initial erreichbar per SSH und vorerst ohne DNS.

## Basisprüfung

```bash
ssh alveran
cat /etc/os-release
apt update
apt upgrade -y
```

## Docker Engine + Compose Plugin

```bash
apt update
apt install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable" \
  > /etc/apt/sources.list.d/docker.list
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
docker --version
docker compose version
```

## Firewall

Minimal für den aktuellen IP-basierten Betrieb:

```bash
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 3300/tcp
ufw enable
ufw status
```

## Zielverzeichnis für Deploys

```bash
mkdir -p /opt/namenschmiede/infra
cd /opt/namenschmiede
```

## SSH-Zugang für GitHub Actions

Empfohlen ist ein eigener Deploy-User. Minimal geht auch ein bestehender User mit Docker-Rechten.

```bash
adduser --disabled-password --gecos "" deploy
usermod -aG docker deploy
mkdir -p /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
touch /home/deploy/.ssh/authorized_keys
chmod 600 /home/deploy/.ssh/authorized_keys
chown -R deploy:deploy /home/deploy/.ssh
```

Danach den Public Key aus dem GitHub-Secret-Paar in
`/home/deploy/.ssh/authorized_keys` eintragen.

## GHCR-Zugriff testen

```bash
echo "<ghcr-token>" | docker login ghcr.io -u "<ghcr-username>" --password-stdin
docker pull ghcr.io/cmdhertel/aventurische-namensschmiede/namegen-web:latest
```

## Prüfung nach erstem CI-Deploy

```bash
cd /opt/namenschmiede
docker compose --env-file infra/.env -f infra/docker-compose.prod.yml ps
curl http://<SERVER-IP>/health
curl -u admin:<passwort> http://<SERVER-IP>/
```

Grafana ist danach direkt per IP erreichbar:

```bash
http://<SERVER-IP>:3300
```

## Spätere Härtung

Sobald DNS vorhanden ist:

- Non-root Deploy-User anlegen
- SSH-Login für Root deaktivieren
- Reverse Proxy mit TLS davor setzen
- Security Headers und Rate Limiting ergänzen

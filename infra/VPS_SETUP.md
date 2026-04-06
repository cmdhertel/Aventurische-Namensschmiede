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
ufw enable
ufw status
```

## Repository ausrollen

```bash
cd /root
git clone https://github.com/cmdhertel/Aventurische-Namensschmiede.git
cd Aventurische-Namensschmiede
cp infra/.env.example infra/.env
vim infra/.env
docker compose --env-file infra/.env -f infra/docker-compose.prod.yml up -d --build
```

## Prüfung

```bash
curl http://<SERVER-IP>/health
curl -u admin:<passwort> http://<SERVER-IP>/
docker compose --env-file infra/.env -f infra/docker-compose.prod.yml ps
```

## Spätere Härtung

Sobald DNS vorhanden ist:

- Non-root Deploy-User anlegen
- SSH-Login für Root deaktivieren
- Reverse Proxy mit TLS davor setzen
- Security Headers und Rate Limiting ergänzen

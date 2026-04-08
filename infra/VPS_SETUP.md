# VPS Setup Guide

Zielsystem: Ubuntu 24.04 LTS, per SSH erreichbar und mit Domain auf die Server-IP.

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

Minimal für HTTPS-Betrieb mit Let's Encrypt:

```bash
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
ufw status
```

## Zielverzeichnis für Deploys

```bash
mkdir -p /opt/namenschmiede/infra
mkdir -p /opt/namenschmiede/certbot/conf
mkdir -p /opt/namenschmiede/certbot/www
cd /opt/namenschmiede
```

## DNS prüfen

Vor der Zertifikatsausstellung muss die Domain bereits auf die Server-IP zeigen:

```bash
dig +short namen.example.de
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
curl http://namen.example.de/health
curl -u admin:<passwort> http://namen.example.de/
```

Nach ausgestelltem Zertifikat:

```bash
curl https://namen.example.de/health
curl -u admin:<passwort> https://namen.example.de/
```

Grafana ist danach unter `https://namen.example.de/grafana/` erreichbar.

## Spätere Härtung

- Non-root Deploy-User anlegen
- SSH-Login für Root deaktivieren
- Renewal automatisieren
- Security Headers und Rate Limiting ergänzen

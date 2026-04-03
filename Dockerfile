# ── Stage 1: Build ────────────────────────────────────────────────────────────
FROM python:3.12-alpine AS builder

# Native build deps (reportlab braucht freetype/zlib zum Kompilieren)
RUN apk add --no-cache \
    gcc \
    musl-dev \
    zlib-dev \
    freetype-dev \
    libpng-dev

WORKDIR /build

# Venv isoliert die Installation sauber vom System-Python
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Erst nur Metadaten, damit Layer-Cache bei reinen Code-Änderungen greift
COPY pyproject.toml ./
COPY src/ src/

RUN pip install --no-cache-dir .

# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.12-alpine

# Nur Runtime-Bibliotheken (keine Build-Tools)
RUN apk add --no-cache \
    freetype \
    zlib \
    libpng

# Kein Root-Betrieb
RUN adduser -D -u 1000 namegen

# Venv aus Build-Stage übernehmen
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# PDF-Ausgabe landet hier (Volume-Mount möglich)
WORKDIR /output

USER namegen

ENTRYPOINT ["namegen"]
CMD ["--help"]

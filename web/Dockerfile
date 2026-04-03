# ── Stage 1: Tailwind CSS kompilieren ────────────────────────────────────────
FROM node:20-alpine AS css-builder

WORKDIR /build

COPY web/package.json web/tailwind.config.js ./
RUN npm install

COPY web/templates/ templates/
COPY web/static/input.css static/input.css

RUN npx tailwindcss -i static/input.css -o static/app.css --minify


# ── Stage 2: Python-Paket bauen ───────────────────────────────────────────────
FROM python:3.12-alpine AS py-builder

RUN apk add --no-cache gcc musl-dev zlib-dev freetype-dev libpng-dev

WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml ./
COPY src/ src/

RUN pip install --no-cache-dir \
    . \
    "fastapi>=0.115" \
    "uvicorn[standard]>=0.30" \
    "jinja2>=3.1" \
    "python-multipart>=0.0.9"


# ── Stage 3: Runtime ──────────────────────────────────────────────────────────
FROM python:3.12-alpine

# Nur Runtime-Bibliotheken (keine Build-Tools)
RUN apk add --no-cache freetype zlib libpng && \
    adduser -D -u 1000 namegen

COPY --from=py-builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Web-App-Quellcode
COPY web/ /app/

# Kompiliertes CSS überschreibt input.css-Artefakt
COPY --from=css-builder /build/static/app.css /app/static/app.css

WORKDIR /app
USER namegen

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

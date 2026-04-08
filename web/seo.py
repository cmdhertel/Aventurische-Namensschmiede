"""Shared SEO helpers for HTML pages and crawl endpoints."""

from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlsplit

DEFAULT_SITE_NAME = "Aventurische Namensschmiede"
DEFAULT_DESCRIPTION = (
    "Aventurischer Namensgenerator fuer Das Schwarze Auge mit Web-App fuer "
    "Namen, Charaktere, Regionen und Favoriten."
)
DEFAULT_SOCIAL_IMAGE_PATH = "/static/favicon.png"


@dataclass(frozen=True)
class SeoMeta:
    title: str
    description: str
    canonical_url: str
    robots: str
    og_type: str = "website"
    image_url: str | None = None


def _normalized_base_url() -> str:
    raw = os.getenv("APP_BASE_URL", "").strip()
    if not raw:
        return "https://aventurische-namensschmiede.de"
    return raw.rstrip("/")


def _join_url(base_url: str, path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{base_url}{path}"


def build_seo_meta(
    *,
    title: str,
    description: str,
    path: str,
    robots: str = "index,follow",
    image_path: str = DEFAULT_SOCIAL_IMAGE_PATH,
) -> SeoMeta:
    base_url = _normalized_base_url()
    return SeoMeta(
        title=title,
        description=description,
        canonical_url=_join_url(base_url, path),
        robots=robots,
        image_url=_join_url(base_url, image_path),
    )


def site_origin_for_robots() -> str:
    return _normalized_base_url()


def site_host() -> str:
    return urlsplit(_normalized_base_url()).netloc

"""
Stock-photo integration for the Media Library.

Two licensed sources, both safe for commercial use:
  - Openverse  -> NO API KEY required (default). Openly-licensed / public-domain
                  images, filtered to commercially-usable licenses.
  - Pexels     -> optional, used when PEXELS_API_KEY is set and source='pexels'.

`import_photo` downloads the chosen image into the library with its credit
attached, so the proposal's credits page fills itself.
"""
from __future__ import annotations

from django.conf import settings
from django.core.files.base import ContentFile

PEXELS_URL = "https://api.pexels.com/v1/search"
OPENVERSE_URL = "https://api.openverse.org/v1/images/"
USER_AGENT = "LaraProposalStudio/1.0 (+https://www.laratoursandtravels.com)"


def is_enabled() -> bool:
    """Search is always available now — Openverse needs no key."""
    return True


def pexels_enabled() -> bool:
    return bool(getattr(settings, "PEXELS_API_KEY", ""))


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------
def search(query: str, source: str | None = None, per_page: int = 24) -> list[dict]:
    if not query:
        return []
    source = source or "openverse"          # default = no-key source
    if source == "pexels" and pexels_enabled():
        return _search_pexels(query, per_page)
    return _search_openverse(query, per_page)


def _search_openverse(query: str, per_page: int = 24, page: int = 1) -> list[dict]:
    try:
        import requests
    except ImportError:
        return []
    try:
        resp = requests.get(
            OPENVERSE_URL,
            params={
                "q": query,
                "license_type": "commercial",   # only commercially-usable licenses
                "page_size": per_page,
                "page": page,
                "mature": "false",
            },
            headers={"User-Agent": USER_AGENT},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    out = []
    for p in data.get("results", []):
        full = p.get("url", "")
        out.append({
            "id": str(p.get("id", "")),
            "thumb": p.get("thumbnail") or full,
            "full": full,
            "photographer": p.get("creator") or "Unknown",
            "photographer_url": p.get("creator_url") or p.get("foreign_landing_url", ""),
            "width": p.get("width", 0),
            "height": p.get("height", 0),
            "alt": p.get("title") or query,
            "source_label": "Openverse",
            "license": (p.get("license") or "").upper(),
        })
    return out


def _search_pexels(query: str, per_page: int = 24, page: int = 1) -> list[dict]:
    try:
        import requests
    except ImportError:
        return []
    try:
        resp = requests.get(
            PEXELS_URL,
            headers={"Authorization": settings.PEXELS_API_KEY},
            params={"query": query, "per_page": per_page, "page": page},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    out = []
    for photo in data.get("photos", []):
        src = photo.get("src", {})
        out.append({
            "id": str(photo.get("id", "")),
            "thumb": src.get("medium") or src.get("small", ""),
            "full": src.get("large2x") or src.get("large") or src.get("original", ""),
            "photographer": photo.get("photographer", ""),
            "photographer_url": photo.get("photographer_url", ""),
            "width": photo.get("width", 0),
            "height": photo.get("height", 0),
            "alt": photo.get("alt", "") or query,
            "source_label": "Pexels",
            "license": "Pexels License",
        })
    return out


# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------
def import_photo(*, source_id, full_url, photographer, photographer_url,
                 title="", category="destination", provider=None):
    """Download a chosen photo into the Media Library with its credit."""
    from .models import MediaImage

    try:
        import requests
    except ImportError:
        return None

    if not full_url:
        return None

    # Infer the source from the URL so the credit is recorded correctly.
    provider = provider or ("pexels" if "pexels.com" in full_url else "openverse")

    try:
        resp = requests.get(full_url, headers={"User-Agent": USER_AGENT}, timeout=30)
        resp.raise_for_status()
        content = resp.content
    except Exception:
        return None

    img = MediaImage(
        title=title or f"{provider.title()} {source_id}",
        category=category,
        source=provider,
        credit_name=photographer or "Unknown",
        credit_url=photographer_url or "",
        source_id=str(source_id),
    )
    img.image.save(f"{provider}_{source_id}.jpg", ContentFile(content), save=True)
    return img

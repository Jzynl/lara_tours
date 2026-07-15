"""Template helpers for the proposal templates."""
from __future__ import annotations

from pathlib import Path

from django import template

register = template.Library()


def _fieldfile(obj):
    """Resolve a MediaImage or an ImageField/FieldFile down to a file object."""
    if obj is None:
        return None
    # MediaImage instance -> its .image FieldFile
    inner = getattr(obj, "image", None)
    if inner is not None and hasattr(inner, "url"):
        return inner
    if hasattr(obj, "url"):  # already a FieldFile
        return obj
    return None


@register.filter
def media_src(obj, pdf_mode=False):
    """
    Return a usable image src.
    - preview (pdf_mode False): the web URL
    - PDF (pdf_mode True): a local file:// URI so WeasyPrint can read it off disk
    """
    f = _fieldfile(obj)
    if not f:
        return ""
    try:
        if pdf_mode:
            return Path(f.path).as_uri()
        return f.url
    except Exception:
        return ""


@register.filter
def money(value, symbol="$"):
    try:
        return f"{symbol}{float(value):,.2f}"
    except (TypeError, ValueError):
        return f"{symbol}0.00"


@register.filter
def paragraphs(text):
    """Split a text block into a list of paragraphs on blank lines."""
    if not text:
        return []
    return [p.strip() for p in str(text).split("\n\n") if p.strip()]


@register.filter
def lines(text):
    """Split a text block into non-empty lines (for Included/Excluded lists)."""
    if not text:
        return []
    return [ln.strip(" •-\t") for ln in str(text).splitlines() if ln.strip(" •-\t")]

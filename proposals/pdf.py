"""
Render a proposal to PDF.

Primary engine: WeasyPrint — renders the full, branded template
(`proposals/pdf/proposal.html`) exactly like the on-screen preview.

If WeasyPrint (or its GTK libraries) can't be loaded, we automatically fall
back to xhtml2pdf with the simpler template so a download is always possible.
"""
from __future__ import annotations

import os
from io import BytesIO

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.text import slugify

from .models import CompanyProfile


def build_context(proposal, *, pdf_mode: bool) -> dict:
    return {
        "proposal": proposal,
        "company": CompanyProfile.get_solo(),
        "days": list(proposal.days.all()),
        "pricing_items": list(proposal.pricing_items.all()),
        "pdf_mode": pdf_mode,
    }


def render_html(proposal, *, pdf_mode: bool) -> str:
    return render_to_string("proposals/pdf/proposal.html", build_context(proposal, pdf_mode=pdf_mode))


def _link_callback(uri, rel):
    """Resolve /media/ and /static/ URLs to absolute file paths (xhtml2pdf fallback)."""
    for url, root in (
        (getattr(settings, "MEDIA_URL", "/media/"), getattr(settings, "MEDIA_ROOT", "")),
        (getattr(settings, "STATIC_URL", "/static/"), str(settings.BASE_DIR / "static")),
    ):
        if url and uri.startswith(url):
            path = os.path.join(root, uri[len(url):])
            if os.path.isfile(path):
                return path
    if uri.startswith("static/"):
        path = str(settings.BASE_DIR / uri)
        if os.path.isfile(path):
            return path
    return uri


def _render_weasyprint(proposal) -> bytes:
    from weasyprint import HTML  # imported lazily so a missing lib doesn't crash the app
    html = render_html(proposal, pdf_mode=True)
    return HTML(string=html, base_url=str(settings.BASE_DIR)).write_pdf()


def _render_xhtml2pdf(proposal) -> bytes:
    from xhtml2pdf import pisa
    html = render_to_string("proposals/pdf/proposal_simple.html",
                            build_context(proposal, pdf_mode=False))
    buf = BytesIO()
    result = pisa.CreatePDF(html, dest=buf, link_callback=_link_callback, encoding="utf-8")
    if result.err:
        raise RuntimeError("PDF generation failed while rendering the proposal.")
    return buf.getvalue()


def render_pdf(proposal) -> bytes:
    """Return the proposal as PDF bytes. Prefer WeasyPrint; fall back to xhtml2pdf."""
    try:
        return _render_weasyprint(proposal)
    except Exception:
        # WeasyPrint or its GTK libraries unavailable — use the simpler engine.
        try:
            return _render_xhtml2pdf(proposal)
        except Exception as exc:
            raise RuntimeError(
                "Could not generate the PDF. Install WeasyPrint (with GTK) for the "
                "full design, or xhtml2pdf (pip install xhtml2pdf) for the simple one."
            ) from exc


def pdf_filename(proposal) -> str:
    ref = proposal.ref_number.replace(".", "-")
    client = slugify(proposal.client_name) or "client"
    return f"Proposal_{ref}_{client}.pdf"
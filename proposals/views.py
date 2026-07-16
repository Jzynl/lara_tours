from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from . import images as stock
from . import pdf as pdf_service
from .forms import BookingForm, NewsletterForm, ReviewForm
from .models import (
    Agent, Booking, CompanyProfile, Day, Destination, DestinationImage, FAQ,
    HeroSlide, JournalPost, MediaImage, NewsletterSubscriber, Package, PricingItem, Proposal, Review,
)


# ===========================================================================
# PUBLIC SITE
# ===========================================================================
def public_home(request):
    company = CompanyProfile.get_solo()
    slides = list(HeroSlide.objects.filter(is_active=True))
    hero_img = company.hero_image if company.hero_image else None
    if not hero_img and not slides:
        for d in Destination.objects.all():
            imgs = d.ordered_images()
            if imgs:
                hero_img = imgs[0]
                break
    return render(request, "proposals/public/home.html", {
        "hero_slides": slides,
        "hero_img": hero_img,
        "packages": Package.objects.filter(is_active=True, is_featured=True)[:3]
                    or Package.objects.filter(is_active=True)[:3],
        "destinations": Destination.objects.exclude(description="").order_by("name")[:10],
        "posts": JournalPost.objects.filter(published=True)[:3],
        "reviews": Review.objects.filter(approved=True)[:3],
        "faqs": FAQ.objects.all()[:5],
        "newsletter_form": NewsletterForm(),
    })


def public_destinations(request):
    destinations = Destination.objects.all().order_by("region", "name")
    groups = {}
    for d in destinations:
        groups.setdefault(d.region or "Other", []).append(d)
    return render(request, "proposals/public/destinations.html", {"groups": groups})


def public_destination(request, pk):
    destination = get_object_or_404(Destination, pk=pk)
    photos = destination.ordered_images()
    more = (Destination.objects.filter(region=destination.region)
            .exclude(pk=destination.pk)[:3]) if destination.region else []
    return render(request, "proposals/public/destination_detail.html",
                  {"destination": destination, "photos": photos, "more": more})


def packages(request):
    return render(request, "proposals/public/packages.html",
                  {"packages": Package.objects.filter(is_active=True)})


def package_detail(request, slug):
    package = get_object_or_404(Package, slug=slug, is_active=True)
    return render(request, "proposals/public/package_detail.html", {
        "package": package,
        "gallery": package.gallery.all(),
        "days": package.days.all(),
        "rates": package.rates.all(),
    })


def journal(request):
    return render(request, "proposals/public/journal.html",
                  {"posts": JournalPost.objects.filter(published=True)})


def journal_post(request, slug):
    post = get_object_or_404(JournalPost, slug=slug, published=True)
    more = JournalPost.objects.filter(published=True).exclude(pk=post.pk)[:3]
    return render(request, "proposals/public/journal_post.html", {"post": post, "more": more})


def faqs(request):
    return render(request, "proposals/public/faq.html", {"faqs": FAQ.objects.all()})


def reviews(request):
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            form.save()  # approved=False until staff approve
            messages.success(request, "Thank you! Your review will appear once approved.")
            return redirect("reviews")
    else:
        form = ReviewForm()
    return render(request, "proposals/public/reviews.html", {
        "reviews": Review.objects.filter(approved=True),
        "form": form,
    })


def newsletter_subscribe(request):
    if request.method == "POST":
        form = NewsletterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "You're subscribed — welcome aboard!")
        else:
            NewsletterSubscriber.objects.get_or_create(email=request.POST.get("email", "").strip())
            messages.success(request, "You're subscribed — welcome aboard!")
    return redirect(request.POST.get("next") or "home")


def book(request):
    initial = {}
    package = None
    dest_id = request.GET.get("destination")
    if dest_id:
        initial["destination"] = dest_id
    pkg = request.GET.get("package")
    if pkg:
        package = Package.objects.filter(slug=pkg, is_active=True).first()
        if package:
            initial["trip_title"] = package.title
            if package.destination_id:
                initial["destination"] = package.destination_id
    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save()
            return redirect("booking_status", token=booking.token)
        package = Package.objects.filter(slug=request.POST.get("package_slug", ""),
                                         is_active=True).first()
    else:
        form = BookingForm(initial=initial)
    return render(request, "proposals/public/book.html", {"form": form, "package": package})


def booking_status(request, token):
    booking = get_object_or_404(Booking, token=token)
    return render(request, "proposals/public/booking_status.html", {"booking": booking})


def about(request):
    return render(request, "proposals/public/about.html", {})


def contact(request):
    return render(request, "proposals/public/contact.html", {})


# ===========================================================================
# STAFF — PROPOSAL STUDIO
# ===========================================================================
@staff_member_required
def proposal_list(request):
    proposals = Proposal.objects.all()
    q = request.GET.get("q", "").strip()
    if q:
        proposals = proposals.filter(client_name__icontains=q) | proposals.filter(title__icontains=q)
    status = request.GET.get("status", "").strip()
    if status:
        proposals = proposals.filter(status=status)
    open_bookings = Booking.objects.exclude(status__in=["paid", "completed", "cancelled"]).count()
    return render(request, "proposals/home.html", {
        "proposals": proposals.distinct(),
        "q": q,
        "status": status,
        "status_choices": Proposal.STATUS_CHOICES,
        "open_bookings": open_bookings,
    })


@staff_member_required
def proposal_detail(request, pk):
    proposal = get_object_or_404(Proposal, pk=pk)
    context = pdf_service.build_context(proposal, pdf_mode=False)
    context["is_preview"] = True
    return render(request, "proposals/pdf/proposal.html", context)


@staff_member_required
def proposal_pdf(request, pk):
    proposal = get_object_or_404(Proposal, pk=pk)
    try:
        data = pdf_service.render_pdf(proposal)
    except RuntimeError as exc:
        messages.error(request, str(exc))
        return redirect("proposal_detail", pk=pk)
    response = HttpResponse(data, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{pdf_service.pdf_filename(proposal)}"'
    return response


@staff_member_required
def stock_search(request):
    query = request.GET.get("q", "").strip()
    results = stock.search(query) if query else []
    destinations = Destination.objects.all()
    return render(request, "proposals/stock_search.html", {
        "query": query,
        "results": results,
        "enabled": stock.is_enabled(),
        "destinations": destinations,
    })


@staff_member_required
def stock_import(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST required"}, status=405)
    img = stock.import_photo(
        source_id=request.POST.get("source_id", ""),
        full_url=request.POST.get("full_url", ""),
        photographer=request.POST.get("photographer", ""),
        photographer_url=request.POST.get("photographer_url", ""),
        title=request.POST.get("title", ""),
        category="destination",
    )
    if not img:
        return JsonResponse({"ok": False, "error": "Import failed — check your network / Pexels key."}, status=400)
    dest_id = request.POST.get("destination", "")
    if dest_id:
        destination = Destination.objects.filter(pk=dest_id).first()
        if destination:
            order = destination.destinationimage_set.count()
            DestinationImage.objects.create(destination=destination, image=img, order=order)
            return JsonResponse({"ok": True, "message": f"Added to {destination.name}"})
    return JsonResponse({"ok": True, "message": "Saved to library"})


# ===========================================================================
# STAFF — custom itinerary builder (the "Create New Itinerary" page)
# ===========================================================================
from decimal import Decimal, InvalidOperation
import datetime as _dt

INCLUSION_OPTIONS = [
    "Accommodation", "Meals as per itinerary", "Transport & transfers", "Professional Guide",
    "Game drives (4x4)", "Park Fees", "Drinking Water", "Airport Transfers",
    "Boat Transfers", "Entry Fees", "International Flights", "Domestic Flights",
    "Visa Fees", "Travel Insurance", "Tips / Gratuities", "Personal Expenses",
    "Laundry", "Telephone Calls", "Souvenirs", "Optional Activities",
]
DEFAULT_INCLUDED = {"Accommodation", "Meals as per itinerary", "Transport & transfers",
                    "Professional Guide", "Airport Transfers", "Drinking Water"}
CURRENCY_SYMBOLS = {"USD": "$", "EUR": "€", "GBP": "£", "TZS": "TSh", "KES": "KSh"}
MEAL_MAP = {"BB": (True, False, False), "HB": (True, False, True), "FB": (True, True, True), "AI": (True, True, True)}


def _dec(v):
    try:
        return Decimal(str(v).strip() or "0")
    except (InvalidOperation, AttributeError):
        return Decimal("0")


def _pdate(v):
    v = (v or "").strip()
    if not v:
        return None
    try:
        return _dt.date.fromisoformat(v)
    except ValueError:
        return None


@staff_member_required
def proposal_form(request, pk=None):
    proposal = get_object_or_404(Proposal, pk=pk) if pk else None

    if request.method == "POST":
        p = proposal or Proposal()
        p.title = request.POST.get("tour_name", "").strip() or "Untitled itinerary"
        p.client_name = request.POST.get("client_name", "").strip()
        p.client_title = request.POST.get("client_title", "") or "Mr."
        p.client_nationality = request.POST.get("nationality", "").strip()
        agent_id = request.POST.get("agent") or None
        p.agent = Agent.objects.filter(pk=agent_id).first() if agent_id else None
        p.start_date = _pdate(request.POST.get("start_date"))
        p.end_date = _pdate(request.POST.get("end_date"))
        p.num_adults = int(request.POST.get("num_adults") or 0)
        p.num_children = int(request.POST.get("num_children") or 0)
        p.country = request.POST.get("country", "").strip()
        p.tour_style = request.POST.get("tour_style", "private")
        p.meal_plan = request.POST.get("meal_plan", "")
        p.letter_override = request.POST.get("intro", "").strip()
        p.payment_terms = request.POST.get("notes", "").strip()
        cur = request.POST.get("currency", "USD")
        p.currency = cur
        p.currency_symbol = CURRENCY_SYMBOLS.get(cur, "$")
        p.save()

        # rebuild days
        p.days.all().delete()
        dests = request.POST.getlist("day_destination")
        hotels = request.POST.getlist("day_hotel")
        descs = request.POST.getlist("day_desc")
        b, l, d = MEAL_MAP.get(p.meal_plan, (True, True, True))
        n = len(dests)
        for i in range(n):
            dtype = "arrival" if i == 0 else ("departure" if i == n - 1 else "standard")
            Day.objects.create(
                proposal=p, day_number=i + 1, day_type=dtype,
                destination=Destination.objects.filter(pk=dests[i]).first() if dests[i] else None,
                hotel_name=(hotels[i] if i < len(hotels) else "").strip(),
                narrative=(descs[i] if i < len(descs) else "").strip(),
                meal_breakfast=b, meal_lunch=l, meal_dinner=d,
            )

        # rebuild pricing
        p.pricing_items.all().delete()
        pa, pc = _dec(request.POST.get("price_adult")), _dec(request.POST.get("price_child"))
        order = 1
        if p.num_adults and pa:
            PricingItem.objects.create(proposal=p, label="Adult", quantity=p.num_adults,
                                       unit_cost=pa, markup_pct=Decimal("0"), order=order); order += 1
        if p.num_children and pc:
            PricingItem.objects.create(proposal=p, label="Child", quantity=p.num_children,
                                       unit_cost=pc, markup_pct=Decimal("0"), order=order)

        # inclusions / exclusions
        checked = set(request.POST.getlist("incl"))
        other = request.POST.get("incl_other", "").strip()
        included = [x for x in INCLUSION_OPTIONS if x in checked]
        if other:
            included.append(other)
        excluded = [x for x in INCLUSION_OPTIONS if x not in checked]
        p.included = "\n".join(included)
        p.excluded = "\n".join(excluded)

        cover_id = request.POST.get("cover_image")
        if cover_id:
            p.cover_image = MediaImage.objects.filter(pk=cover_id).first()
        else:
            fd = p.days.order_by("day_number").first()
            imgs = fd.destination.ordered_images() if fd and fd.destination else []
            p.cover_image = imgs[0] if imgs else None
        p.save()

        action = request.POST.get("action", "save")
        messages.success(request, f"Itinerary {p.ref_number} saved.")
        if action == "preview" or action == "generate":
            return redirect("proposal_detail", pk=p.pk)
        return redirect("proposal_list")

    # GET — build context
    days = list(proposal.days.all()) if proposal else []
    checked = set()
    if proposal and proposal.included:
        checked = {x.strip() for x in proposal.included.splitlines()}
    elif not proposal:
        checked = set(DEFAULT_INCLUDED)
    price_adult = price_child = ""
    if proposal:
        for it in proposal.pricing_items.all():
            if it.label.lower().startswith("adult"):
                price_adult = it.unit_cost
            elif it.label.lower().startswith("child"):
                price_child = it.unit_cost

    return render(request, "proposals/proposal_form.html", {
        "proposal": proposal,
        "days": days,
        "agents": Agent.objects.all(),
        "destinations": Destination.objects.all().order_by("region", "name"),
        "media_images": MediaImage.objects.all().order_by("-id"),
        "dest_blurbs": {str(d.pk): d.description for d in Destination.objects.all()},
        "inclusion_options": INCLUSION_OPTIONS,
        "checked_incl": checked,
        "currencies": list(CURRENCY_SYMBOLS.keys()),
        "price_adult": price_adult,
        "price_child": price_child,
        "is_edit": bool(proposal),
    })
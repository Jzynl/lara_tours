"""
Data models for the Lara Tours proposal generator.

Layout mirrors the scope document:
  Catalog   -> Tag, MediaImage, Destination, Hotel, Agent, CompanyProfile
  Proposal  -> Proposal, Day, PricingItem
"""
from __future__ import annotations

import datetime
import uuid
from decimal import Decimal

from django.db import models
from django.urls import reverse
from django.utils.text import slugify


# ---------------------------------------------------------------------------
# Company profile (single row)
# ---------------------------------------------------------------------------
class CompanyProfile(models.Model):
    name = models.CharField(max_length=120, default="Lara Tours and Travels")
    tagline = models.CharField(max_length=120, blank=True, default="Unforgettable Experience")
    logo = models.ImageField(upload_to="brand/", blank=True, null=True)
    hero_image = models.ImageField(upload_to="brand/", blank=True, null=True,
                                   help_text="Homepage banner. Landscape ~1920×1080. Leave blank to use a destination photo.")

    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    whatsapp = models.CharField(max_length=40, blank=True)
    website = models.CharField(max_length=120, blank=True)
    address = models.CharField(max_length=200, blank=True)
    country = models.CharField(max_length=80, blank=True)

    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    tiktok_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    x_url = models.URLField(blank=True)

    about_us = models.TextField(blank=True)
    closing_quote = models.TextField(blank=True)
    closing_quote_author = models.CharField(max_length=120, blank=True)

    currency = models.CharField(max_length=8, default="USD")
    currency_symbol = models.CharField(max_length=4, default="$")

    # Booking / payment (manual Lipa Namba flow)
    payment_provider = models.CharField(max_length=60, blank=True, default="Selcom Lipa Namba")
    lipa_namba = models.CharField(max_length=40, blank=True, help_text="Your Lipa Namba / till number shown to clients.")
    deposit_percent = models.PositiveIntegerField(default=40)
    payment_instructions = models.TextField(
        blank=True,
        default=("Pay using M-Pesa, Tigo Pesa, Airtel Money or your bank to the number "
                 "above, then keep your confirmation SMS. We'll confirm your booking as "
                 "soon as payment is received."),
    )

    primary_color = models.CharField(max_length=9, default="#2f4d1e")
    accent_color = models.CharField(max_length=9, default="#e8771c")

    # Defaults copied onto each new proposal (then editable per proposal).
    default_included = models.TextField(blank=True)
    default_excluded = models.TextField(blank=True)
    default_payment_terms = models.CharField(max_length=255, blank=True)

    # Merge template for the cover letter. Use {placeholders}; see Proposal.letter_context.
    letter_template = models.TextField(
        blank=True,
        default=(
            "Thank you for considering our {title}. We are delighted to offer this "
            "customised journey for {travelers}.\n\n"
            "Your trip begins on {start_date} in {start_destination}. It spans "
            "{num_days} days, ending on {end_date} in {end_destination}.\n\n"
            "The team and I are here to answer any questions you may have. "
            "We look forward to your response."
        ),
    )

    class Meta:
        verbose_name = "Company profile"
        verbose_name_plural = "Company profile"

    def __str__(self) -> str:
        return self.name

    @classmethod
    def get_solo(cls) -> "CompanyProfile":
        obj = cls.objects.first()
        if obj is None:
            obj = cls.objects.create()
        return obj

    @property
    def whatsapp_digits(self) -> str:
        """Digits only, for wa.me links."""
        return "".join(ch for ch in (self.whatsapp or self.phone or "") if ch.isdigit())

    @property
    def social_links(self):
        out = []
        for label, url in [("Facebook", self.facebook_url), ("Instagram", self.instagram_url),
                           ("TikTok", self.tiktok_url), ("YouTube", self.youtube_url), ("X", self.x_url)]:
            if url:
                out.append((label, url))
        return out


# ---------------------------------------------------------------------------
# Agents / consultants
# ---------------------------------------------------------------------------
class Agent(models.Model):
    name = models.CharField(max_length=120)
    title = models.CharField(max_length=120, blank=True, default="Travel Consultant")
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    signature = models.ImageField(upload_to="agents/", blank=True, null=True)
    photo = models.ImageField(upload_to="agents/", blank=True, null=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


# ---------------------------------------------------------------------------
# Media library
# ---------------------------------------------------------------------------
class Tag(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class MediaImage(models.Model):
    SOURCE_UPLOAD = "upload"
    SOURCE_PEXELS = "pexels"
    SOURCE_OPENVERSE = "openverse"
    SOURCE_CHOICES = [
        (SOURCE_UPLOAD, "Upload"),
        (SOURCE_PEXELS, "Pexels"),
        (SOURCE_OPENVERSE, "Openverse"),
    ]

    CATEGORY_CHOICES = [
        ("destination", "Destination"),
        ("hero", "Hero / cover"),
        ("mood", "Mood"),
        ("food", "Food"),
        ("culture", "Culture"),
    ]

    title = models.CharField(max_length=160, blank=True)
    image = models.ImageField(upload_to="library/")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="destination")
    tags = models.ManyToManyField(Tag, blank=True, related_name="images")

    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default=SOURCE_UPLOAD)
    credit_name = models.CharField(max_length=160, blank=True)
    credit_url = models.URLField(blank=True)
    source_id = models.CharField(max_length=60, blank=True)

    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Library image"

    def __str__(self) -> str:
        return self.title or f"Image #{self.pk}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image and (not self.width or not self.height):
            try:
                self.width = self.image.width
                self.height = self.image.height
                super().save(update_fields=["width", "height"])
            except Exception:
                pass

    @property
    def credit_label(self) -> str:
        if self.credit_name and self.source in (self.SOURCE_PEXELS, self.SOURCE_OPENVERSE):
            return f"{self.credit_name} ({self.get_source_display()})"
        return self.credit_name


# ---------------------------------------------------------------------------
# Destinations
# ---------------------------------------------------------------------------
class Destination(models.Model):
    name = models.CharField(max_length=120)
    region = models.CharField(max_length=120, blank=True)
    country = models.CharField(max_length=80, blank=True)
    description = models.TextField(
        blank=True, help_text="Evergreen, atmospheric blurb reused on every proposal."
    )
    images = models.ManyToManyField(
        MediaImage, through="DestinationImage", related_name="destinations", blank=True
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def ordered_images(self):
        return [di.image for di in self.destinationimage_set.select_related("image")]


class DestinationImage(models.Model):
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE)
    image = models.ForeignKey(MediaImage, on_delete=models.CASCADE)
    caption = models.CharField(max_length=160, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return f"{self.destination} · {self.image}"


# ---------------------------------------------------------------------------
# Hotels (text-first)
# ---------------------------------------------------------------------------
class Hotel(models.Model):
    name = models.CharField(max_length=160)
    hotel_type = models.CharField(max_length=60, blank=True, default="Hotel")
    location = models.CharField(max_length=160, blank=True)
    destination = models.ForeignKey(
        Destination, on_delete=models.SET_NULL, null=True, blank=True, related_name="hotels"
    )
    description = models.TextField(blank=True)
    image = models.ForeignKey(
        MediaImage, on_delete=models.SET_NULL, null=True, blank=True, related_name="hotels"
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


# ---------------------------------------------------------------------------
# Proposal
# ---------------------------------------------------------------------------
class Proposal(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("sent", "Sent"),
        ("confirmed", "Confirmed"),
    ]
    TITLE_CHOICES = [("Mr.", "Mr."), ("Mrs.", "Mrs."), ("Ms.", "Ms."), ("Dr.", "Dr."), ("", "—")]

    # Reference number parts -> "YYYY-NNNN.V"
    ref_year = models.PositiveIntegerField(blank=True)
    ref_seq = models.PositiveIntegerField(blank=True)
    ref_version = models.PositiveIntegerField(default=1)

    title = models.CharField(max_length=160, help_text='e.g. "Creating Memories in Zanzibar"')
    cover_eyebrow = models.CharField(
        max_length=120, blank=True, default="Creating memories in"
    )

    client_title = models.CharField(max_length=8, choices=TITLE_CHOICES, blank=True, default="Mr.")
    client_name = models.CharField(max_length=160)
    client_nationality = models.CharField(max_length=80, blank=True)

    num_adults = models.PositiveIntegerField(default=2)
    num_children = models.PositiveIntegerField(default=0)

    start_date = models.DateField()
    end_date = models.DateField()

    start_destination = models.ForeignKey(
        Destination, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    end_destination = models.ForeignKey(
        Destination, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True)
    cover_image = models.ForeignKey(
        MediaImage, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    currency = models.CharField(max_length=8, default="USD")
    currency_symbol = models.CharField(max_length=4, default="$")

    country = models.CharField(max_length=80, blank=True)
    tour_style = models.CharField(max_length=10, blank=True, default="private",
                                  choices=[("private", "Private tour"), ("group", "Group tour")])
    meal_plan = models.CharField(max_length=4, blank=True,
                                 choices=[("BB", "Bed & Breakfast"), ("HB", "Half Board"),
                                          ("FB", "Full Board"), ("AI", "All Inclusive")])
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="draft")

    # Copied from CompanyProfile defaults on creation, then editable here.
    letter_override = models.TextField(blank=True, help_text="Leave blank to use the company template.")
    included = models.TextField(blank=True)
    excluded = models.TextField(blank=True)
    payment_terms = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-ref_year", "-ref_seq", "-ref_version"]
        unique_together = [("ref_year", "ref_seq", "ref_version")]

    def __str__(self) -> str:
        return f"{self.ref_number} — {self.client_fullname}"

    # -- reference number ---------------------------------------------------
    def save(self, *args, **kwargs):
        company = CompanyProfile.get_solo()
        if not self.ref_year:
            self.ref_year = (self.start_date or datetime.date.today()).year
        if not self.ref_version:
            self.ref_version = 1
        if not self.ref_seq:
            last = (
                Proposal.objects.filter(ref_year=self.ref_year)
                .order_by("-ref_seq")
                .first()
            )
            seq = (last.ref_seq + 1) if last else 1
            while Proposal.objects.filter(
                ref_year=self.ref_year, ref_seq=seq, ref_version=self.ref_version
            ).exclude(pk=self.pk).exists():
                seq += 1
            self.ref_seq = seq
        # First save copies branding defaults across.
        first_time = self._state.adding
        if first_time:
            self.currency = self.currency or company.currency
            self.currency_symbol = self.currency_symbol or company.currency_symbol
            self.included = self.included or company.default_included
            self.excluded = self.excluded or company.default_excluded
            self.payment_terms = self.payment_terms or company.default_payment_terms
        super().save(*args, **kwargs)

    @property
    def ref_number(self) -> str:
        if self.ref_year and self.ref_seq:
            return f"{self.ref_year}-{self.ref_seq:04d}.{self.ref_version}"
        return "unsaved"

    # -- derived facts ------------------------------------------------------
    @property
    def client_fullname(self) -> str:
        return f"{self.client_title} {self.client_name}".strip()

    @property
    def num_days(self) -> int:
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return self.days.count()

    @property
    def nights(self) -> int:
        return max(self.num_days - 1, 0)

    @property
    def tour_length_label(self) -> str:
        d, n = self.num_days, self.nights
        return f"{d} Day{'s' if d != 1 else ''} / {n} Night{'s' if n != 1 else ''}"

    @property
    def travelers_label(self) -> str:
        parts = []
        if self.num_adults:
            parts.append(f"{self.num_adults} Adult{'s' if self.num_adults != 1 else ''}")
        if self.num_children:
            parts.append(f"{self.num_children} Child{'ren' if self.num_children != 1 else ''}")
        return " & ".join(parts) if parts else "—"

    # -- pricing ------------------------------------------------------------
    @property
    def total(self) -> Decimal:
        return sum((item.line_total for item in self.pricing_items.all()), Decimal("0.00"))

    # -- letter -------------------------------------------------------------
    def letter_context(self) -> dict:
        company = CompanyProfile.get_solo()
        fmt = "%B %-d, %Y"
        try:
            start = self.start_date.strftime(fmt)
            end = self.end_date.strftime(fmt)
        except (AttributeError, ValueError):
            # %-d is not portable to Windows; fall back.
            start = self.start_date.strftime("%B %d, %Y") if self.start_date else ""
            end = self.end_date.strftime("%B %d, %Y") if self.end_date else ""
        return {
            "title": self.title,
            "client_title": self.client_title,
            "client_name": self.client_name,
            "client_fullname": self.client_fullname,
            "travelers": self.travelers_label,
            "num_days": self.num_days,
            "nights": self.nights,
            "tour_length": self.tour_length_label,
            "start_date": start,
            "end_date": end,
            "start_destination": self.start_destination.name if self.start_destination else "",
            "end_destination": self.end_destination.name if self.end_destination else "",
            "agent_name": self.agent.name if self.agent else "",
            "company_name": company.name,
        }

    @property
    def rendered_letter(self) -> str:
        company = CompanyProfile.get_solo()
        template = self.letter_override or company.letter_template
        ctx = self.letter_context()

        class _Safe(dict):
            def __missing__(self, key):  # leave unknown placeholders untouched
                return "{" + key + "}"

        try:
            return template.format_map(_Safe(ctx))
        except (ValueError, IndexError):
            return template

    @property
    def credit_images(self):
        """Distinct credited images used anywhere in this proposal (for the colophon)."""
        seen, out = set(), []
        candidates = []
        if self.cover_image:
            candidates.append(self.cover_image)
        for day in self.days.all():
            candidates.extend(day.photos())
        for img in candidates:
            if img and img.credit_name and img.pk not in seen:
                seen.add(img.pk)
                out.append(img)
        return out

    def get_absolute_url(self):
        return reverse("proposal_detail", args=[self.pk])


# ---------------------------------------------------------------------------
# Days
# ---------------------------------------------------------------------------
class Day(models.Model):
    DAY_TYPES = [
        ("standard", "Standard"),
        ("arrival", "Arrival"),
        ("leisure", "Leisure"),
        ("departure", "Departure"),
    ]

    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name="days")
    day_number = models.PositiveIntegerField(default=1)
    day_type = models.CharField(max_length=12, choices=DAY_TYPES, default="standard")

    destination = models.ForeignKey(
        Destination, on_delete=models.SET_NULL, null=True, blank=True
    )
    title = models.CharField(max_length=160, blank=True, help_text="Defaults to the destination name.")
    narrative = models.TextField(blank=True)

    hotel = models.ForeignKey(Hotel, on_delete=models.SET_NULL, null=True, blank=True)
    hotel_name = models.CharField(max_length=160, blank=True, help_text="Free-text hotel/lodge (used if no linked hotel).")
    room_config = models.CharField(
        max_length=200, blank=True, help_text='e.g. "2× Deluxe Room"'
    )
    accommodation_blurb = models.CharField(max_length=255, blank=True)

    meal_breakfast = models.BooleanField(default=False)
    meal_lunch = models.BooleanField(default=False)
    meal_dinner = models.BooleanField(default=False)

    class Meta:
        ordering = ["day_number"]
        unique_together = [("proposal", "day_number")]

    def __str__(self) -> str:
        return f"Day {self.day_number} — {self.display_title}"

    @property
    def display_title(self) -> str:
        if self.title:
            return self.title
        if self.day_type == "departure":
            return "Departure"
        if self.day_type == "leisure":
            return "Leisure Day"
        return self.destination.name if self.destination else f"Day {self.day_number}"

    @property
    def date(self):
        if self.proposal and self.proposal.start_date:
            return self.proposal.start_date + datetime.timedelta(days=self.day_number - 1)
        return None

    @property
    def display_narrative(self) -> str:
        """Use the day's own narrative, else fall back to the destination's blurb."""
        if self.narrative:
            return self.narrative
        if self.destination and self.destination.description:
            return self.destination.description
        return ""

    @property
    def hotel_display(self) -> str:
        if self.hotel_name:
            return self.hotel_name
        if self.hotel:
            return self.hotel.name
        return ""

    @property
    def meal_plan_label(self) -> str:
        meals = []
        if self.meal_breakfast:
            meals.append("Breakfast")
        if self.meal_lunch:
            meals.append("Lunch")
        if self.meal_dinner:
            meals.append("Dinner")
        if not meals:
            return "Arrangement at own"
        if len(meals) == 1:
            return meals[0]
        return ", ".join(meals[:-1]) + " & " + meals[-1]

    @property
    def board_label(self) -> str:
        """Show the proposal's chosen board basis (Half Board, etc.), not the meal breakdown."""
        if self.proposal_id and self.proposal.meal_plan:
            return self.proposal.get_meal_plan_display()
        return self.meal_plan_label

    def photos(self):
        from django.conf import settings

        if not self.destination:
            return []
        return self.destination.ordered_images()[: settings.DAY_PHOTO_COUNT]


# ---------------------------------------------------------------------------
# Pricing
# ---------------------------------------------------------------------------
class PricingItem(models.Model):
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name="pricing_items")
    label = models.CharField(max_length=120, help_text='e.g. "Adult", "Child", "Transfer"')
    quantity = models.PositiveIntegerField(default=1)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    markup_pct = models.DecimalField(
        max_digits=6, decimal_places=2, default=Decimal("0.00"),
        help_text="Percent added to cost to get the client price.",
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return f"{self.quantity}× {self.label}"

    @property
    def unit_price(self) -> Decimal:
        price = self.unit_cost * (Decimal("1") + (self.markup_pct / Decimal("100")))
        return price.quantize(Decimal("0.01"))

    @property
    def line_total(self) -> Decimal:
        return (self.unit_price * self.quantity).quantize(Decimal("0.01"))

    @property
    def line_cost(self) -> Decimal:
        return (self.unit_cost * self.quantity).quantize(Decimal("0.01"))

    @property
    def margin(self) -> Decimal:
        return (self.line_total - self.line_cost).quantize(Decimal("0.01"))


# ---------------------------------------------------------------------------
# Bookings (public site -> staff confirm)
# ---------------------------------------------------------------------------
class Booking(models.Model):
    STATUS_CHOICES = [
        ("pending", "New request"),
        ("quoted", "Quote sent"),
        ("awaiting", "Awaiting payment"),
        ("confirmed", "Confirmed"),
        ("paid", "Paid in full"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    ref_year = models.PositiveIntegerField(blank=True)
    ref_seq = models.PositiveIntegerField(blank=True)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # who
    full_name = models.CharField(max_length=160)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)

    # what
    destination = models.ForeignKey(Destination, on_delete=models.SET_NULL, null=True, blank=True)
    trip_title = models.CharField(max_length=200, blank=True, help_text="Used if no destination is chosen.")
    num_adults = models.PositiveIntegerField(default=2)
    num_children = models.PositiveIntegerField(default=0)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    flexible_dates = models.BooleanField(default=False)
    message = models.TextField(blank=True)

    # money (staff fills the quote)
    quoted_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=8, default="USD")
    currency_symbol = models.CharField(max_length=4, default="$")
    payment_reference = models.CharField(max_length=120, blank=True, help_text="Client's payment / transaction reference.")
    payment_proof = models.ImageField(upload_to="payment_proofs/", null=True, blank=True)

    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="pending")
    linked_proposal = models.ForeignKey(Proposal, on_delete=models.SET_NULL, null=True, blank=True, related_name="bookings")
    staff_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = [("ref_year", "ref_seq")]

    def __str__(self) -> str:
        return f"{self.ref} — {self.full_name}"

    def save(self, *args, **kwargs):
        if not self.ref_year:
            self.ref_year = datetime.date.today().year
        if not self.ref_seq:
            last = Booking.objects.filter(ref_year=self.ref_year).order_by("-ref_seq").first()
            seq = (last.ref_seq + 1) if last else 1
            while Booking.objects.filter(
                ref_year=self.ref_year, ref_seq=seq
            ).exclude(pk=self.pk).exists():
                seq += 1
            self.ref_seq = seq
        if self._state.adding:
            company = CompanyProfile.get_solo()
            self.currency = self.currency or company.currency
            self.currency_symbol = self.currency_symbol or company.currency_symbol
        super().save(*args, **kwargs)

    @property
    def ref(self) -> str:
        if self.ref_year and self.ref_seq:
            return f"BKG-{self.ref_year}-{self.ref_seq:04d}"
        return "unsaved"

    @property
    def trip_label(self) -> str:
        if self.destination:
            return self.destination.name
        return self.trip_title or "Custom trip"

    @property
    def travelers_label(self) -> str:
        parts = []
        if self.num_adults:
            parts.append(f"{self.num_adults} Adult{'s' if self.num_adults != 1 else ''}")
        if self.num_children:
            parts.append(f"{self.num_children} Child{'ren' if self.num_children != 1 else ''}")
        return " & ".join(parts) if parts else "—"

    @property
    def deposit_amount(self):
        if self.quoted_total is None:
            return None
        company = CompanyProfile.get_solo()
        pct = Decimal(company.deposit_percent) / Decimal("100")
        return (self.quoted_total * pct).quantize(Decimal("0.01"))

    @property
    def is_open(self) -> bool:
        return self.status not in ("paid", "completed", "cancelled")

    def get_absolute_url(self):
        return reverse("booking_status", args=[self.token])


# ---------------------------------------------------------------------------
# Marketing content (packages, journal, reviews, FAQ, newsletter)
# ---------------------------------------------------------------------------
def _unique_slug(model, value):
    base = slugify(value)[:200] or "item"
    slug, i = base, 2
    while model.objects.filter(slug=slug).exists():
        slug = f"{base}-{i}"
        i += 1
    return slug


class Package(models.Model):
    """A travel-ready package a client can browse and book directly."""
    KIND_TOUR = "tour"
    KIND_EXPERIENCE = "experience"
    KIND_CHOICES = [(KIND_TOUR, "Multi-day tour"), (KIND_EXPERIENCE, "Local experience")]
    PRICING_FROM = "from"
    PRICING_FIXED = "fixed"
    PRICING_CHOICES = [(PRICING_FROM, "From (seasonal, agent confirms)"),
                       (PRICING_FIXED, "Fixed price (book directly)")]
    CLASS_CHOICES = [("budget", "Budget"), ("midrange", "Mid-range"), ("luxury", "Luxury")]

    title = models.CharField(max_length=160)
    slug = models.SlugField(max_length=210, unique=True, blank=True)
    kind = models.CharField(max_length=12, choices=KIND_CHOICES, default=KIND_TOUR)
    tag = models.CharField(max_length=40, blank=True, help_text='e.g. "Safari", "Beach", "Cultural", "City"')
    summary = models.CharField(max_length=255, blank=True)
    region = models.CharField(max_length=120, blank=True)
    country = models.CharField(max_length=80, blank=True)
    destination = models.ForeignKey(Destination, on_delete=models.SET_NULL, null=True, blank=True)

    duration_days = models.PositiveIntegerField(default=3)
    pricing_mode = models.CharField(max_length=8, choices=PRICING_CHOICES, default=PRICING_FROM)
    price_from = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                     help_text="Shown as 'from' (tours) or the exact price (experiences).")
    currency_symbol = models.CharField(max_length=4, default="$")

    tour_class = models.CharField(max_length=12, choices=CLASS_CHOICES, blank=True)
    accommodation_type = models.CharField(max_length=60, blank=True, help_text='e.g. "Lodge", "Tented camp"')
    is_private = models.BooleanField(default=True)
    can_start_any_day = models.BooleanField(default=True)
    can_customize = models.BooleanField(default=True)
    age_suitability = models.CharField(max_length=80, blank=True, default="Suitable for all ages")

    start_point = models.CharField(max_length=120, blank=True)
    end_point = models.CharField(max_length=120, blank=True)
    activities = models.CharField(max_length=255, blank=True, help_text="e.g. game drives & boat safari")
    transport = models.CharField(max_length=255, blank=True, help_text="e.g. air transfer; open 4x4")
    getting_there = models.TextField(blank=True, help_text="Airport, flights, transfers, pre/post nights.")

    hero_image = models.ForeignKey(MediaImage, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    gallery = models.ManyToManyField(MediaImage, blank=True, related_name="packages")
    video_url = models.URLField(blank=True, help_text="YouTube/Vimeo link (optional).")

    highlights = models.TextField(blank=True, help_text="One highlight per line.")
    body = models.TextField(blank=True, help_text="Overview description.")
    included = models.TextField(blank=True, help_text="One inclusion per line.")
    excluded = models.TextField(blank=True, help_text="One exclusion per line.")

    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _unique_slug(Package, self.title)
        super().save(*args, **kwargs)

    @property
    def highlight_list(self):
        return [h.strip() for h in self.highlights.splitlines() if h.strip()]

    @property
    def included_list(self):
        return [h.strip() for h in self.included.splitlines() if h.strip()]

    @property
    def excluded_list(self):
        return [h.strip() for h in self.excluded.splitlines() if h.strip()]

    @property
    def is_experience(self):
        return self.kind == self.KIND_EXPERIENCE

    @property
    def price_prefix(self):
        return "" if self.pricing_mode == self.PRICING_FIXED else "from "

    @property
    def route_label(self):
        parts = [p for p in [self.start_point,
                             self.destination.name if self.destination else self.region,
                             self.end_point] if p]
        return " → ".join(dict.fromkeys(parts))

    @property
    def duration_label(self):
        n = self.duration_days
        return f"{n} day{'s' if n != 1 else ''}"

    def get_absolute_url(self):
        return reverse("package_detail", args=[self.slug])


class JournalPost(models.Model):
    """Blog / news / journal post — the SEO + traffic engine."""
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=240, unique=True, blank=True)
    category = models.CharField(max_length=60, blank=True, default="Guides")
    cover_image = models.ForeignKey(MediaImage, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    excerpt = models.CharField(max_length=300, blank=True)
    body = models.TextField(blank=True)
    author = models.CharField(max_length=120, blank=True)
    published = models.BooleanField(default=True)
    published_at = models.DateField(default=datetime.date.today)

    class Meta:
        ordering = ["-published_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _unique_slug(JournalPost, self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("journal_post", args=[self.slug])


class Review(models.Model):
    author_name = models.CharField(max_length=120)
    location = models.CharField(max_length=120, blank=True)
    rating = models.PositiveSmallIntegerField(default=5)
    body = models.TextField()
    trip = models.CharField(max_length=160, blank=True)
    approved = models.BooleanField(default=False, help_text="Tick to show on the website.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.author_name} ({self.rating}★)"

    @property
    def stars(self):
        return "★" * int(self.rating) + "☆" * (5 - int(self.rating))


class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.email


class PackageDay(models.Model):
    """A day (or day-range) in a package's fixed itinerary."""
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name="days")
    day_label = models.CharField(max_length=40, help_text='e.g. "Day 1" or "Day 1–2"')
    title = models.CharField(max_length=160, blank=True)
    description = models.TextField(blank=True)
    accommodation = models.CharField(max_length=160, blank=True)
    accommodation_note = models.CharField(max_length=200, blank=True)
    meals = models.CharField(max_length=120, blank=True, help_text='e.g. "All meals" / "Breakfast & lunch"')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.package.title} — {self.day_label}"


class PackageRate(models.Model):
    """One duration row of a package's occupancy price grid (per person)."""
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name="rates")
    duration_label = models.CharField(max_length=60, help_text='e.g. "2 nights / 3 days"')
    price_single = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_double = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_family = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.package.title} — {self.duration_label}"


class HeroSlide(models.Model):
    """An image in the homepage hero slideshow."""
    image = models.ImageField(upload_to="hero/", help_text="Landscape ~1920×1080, under ~500 KB.")
    caption = models.CharField(max_length=120, blank=True, help_text="Optional — not shown, just for your reference.")
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.caption or f"Hero slide {self.pk}"
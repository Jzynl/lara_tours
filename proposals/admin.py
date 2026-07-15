from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html

from . import models


@admin.register(models.CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Identity", {"fields": ("name", "tagline", "logo", "hero_image", "primary_color", "accent_color")}),
        ("Contact", {"fields": ("email", "phone", "whatsapp", "website", "address", "country")}),
        ("Social links", {"fields": ("facebook_url", "instagram_url", "tiktok_url",
                                     "youtube_url", "x_url"), "classes": ("collapse",)}),
        ("Pages", {"fields": ("about_us", "closing_quote", "closing_quote_author")}),
        ("Currency", {"fields": ("currency", "currency_symbol")}),
        ("Booking & payment", {"fields": ("payment_provider", "lipa_namba",
                                          "deposit_percent", "payment_instructions")}),
        ("Proposal defaults", {"fields": ("default_included", "default_excluded",
                                          "default_payment_terms", "letter_template")}),
    )

    def has_add_permission(self, request):
        return not models.CompanyProfile.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(models.Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ("name", "title", "email", "phone")
    search_fields = ("name", "email")


@admin.register(models.Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(models.MediaImage)
class MediaImageAdmin(admin.ModelAdmin):
    list_display = ("thumb", "title", "category", "source", "credit_name", "created_at")
    list_display_links = ("thumb", "title")
    list_filter = ("category", "source", "tags")
    search_fields = ("title", "credit_name", "tags__name")
    filter_horizontal = ("tags",)
    readonly_fields = ("width", "height", "preview")
    # Upload is just: pick a file. Everything else is optional and tucked away.
    fieldsets = (
        (None, {"fields": ("image", "preview", "title", "category", "tags")}),
        ("Credit (optional)", {
            "classes": ("collapse",),
            "fields": ("source", "credit_name", "credit_url", "source_id"),
        }),
    )

    @admin.display(description="")
    def thumb(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:42px;width:60px;object-fit:cover;border-radius:4px">',
                obj.image.url,
            )
        return "—"

    @admin.display(description="Preview")
    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height:240px;border-radius:8px">', obj.image.url)
        return "—"


class DestinationImageInline(admin.TabularInline):
    model = models.DestinationImage
    extra = 1
    autocomplete_fields = ("image",)
    ordering = ("order",)


@admin.register(models.Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ("name", "region", "country", "image_count")
    search_fields = ("name", "region", "country")
    inlines = [DestinationImageInline]

    @admin.display(description="Photos")
    def image_count(self, obj):
        return obj.images.count()


@admin.register(models.Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ("name", "hotel_type", "location", "destination")
    list_filter = ("hotel_type", "destination")
    search_fields = ("name", "location")
    autocomplete_fields = ("image", "destination")


class DayInline(admin.StackedInline):
    model = models.Day
    extra = 1
    ordering = ("day_number",)
    autocomplete_fields = ("destination", "hotel")
    fields = (
        "day_number", "day_type", "destination", "title", "narrative",
        ("hotel", "room_config"), "accommodation_blurb",
        ("meal_breakfast", "meal_lunch", "meal_dinner"),
    )


class PricingItemInline(admin.TabularInline):
    model = models.PricingItem
    extra = 1
    ordering = ("order",)
    readonly_fields = ("unit_price", "line_total", "margin")
    fields = ("order", "label", "quantity", "unit_cost", "markup_pct",
              "unit_price", "line_total", "margin")


@admin.register(models.Proposal)
class ProposalAdmin(admin.ModelAdmin):
    """Proposals are created/edited in the Studio builder, not here."""
    def changelist_view(self, request, extra_context=None):
        return redirect("proposal_list")

    def add_view(self, request, form_url="", extra_context=None):
        return redirect("proposal_new")

    def change_view(self, request, object_id, form_url="", extra_context=None):
        return redirect("proposal_edit", pk=object_id)

    list_display = ("ref_number", "client_fullname", "title", "status",
                    "num_days", "total_display", "links")
    list_filter = ("status", "ref_year", "agent")
    search_fields = ("client_name", "title")
    autocomplete_fields = ("start_destination", "end_destination", "cover_image")
    inlines = [DayInline, PricingItemInline]
    readonly_fields = ("ref_number", "tour_length_label", "travelers_label", "total_display")
    actions = ["duplicate_proposals"]
    fieldsets = (
        ("Reference", {"fields": ("ref_number", "status")}),
        ("Headline", {"fields": ("title", "cover_eyebrow", "cover_image")}),
        ("Client", {"fields": (("client_title", "client_name"),
                               ("num_adults", "num_children"), "travelers_label")}),
        ("Dates & route", {"fields": (("start_date", "end_date"), "tour_length_label",
                                      ("start_destination", "end_destination"), "agent")}),
        ("Currency", {"fields": ("currency", "currency_symbol")}),
        ("Pricing summary", {"fields": ("total_display",)}),
        ("Letter & terms", {"fields": ("letter_override", "included", "excluded", "payment_terms"),
                            "classes": ("collapse",)}),
    )

    @admin.display(description="Total")
    def total_display(self, obj):
        if obj.pk:
            return f"{obj.currency_symbol}{obj.total:,.2f}"
        return "—"

    @admin.display(description="Open")
    def links(self, obj):
        if not obj.pk:
            return ""
        preview = reverse("proposal_detail", args=[obj.pk])
        pdf = reverse("proposal_pdf", args=[obj.pk])
        return format_html(
            '<a href="{}">preview</a> · <a href="{}">PDF</a>', preview, pdf
        )

    @admin.action(description="Duplicate selected proposals")
    def duplicate_proposals(self, request, queryset):
        for proposal in queryset:
            days = list(proposal.days.all())
            items = list(proposal.pricing_items.all())
            proposal.pk = None
            proposal.ref_seq = None
            proposal.ref_version = 1
            proposal.status = "draft"
            proposal._state.adding = True
            proposal.save()
            for d in days:
                d.pk = None
                d.proposal = proposal
                d.save()
            for it in items:
                it.pk = None
                it.proposal = proposal
                it.save()
        self.message_user(request, f"Duplicated {queryset.count()} proposal(s).")


@admin.register(models.Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("ref", "full_name", "trip_label", "travelers_label",
                    "status", "quoted_total", "created_at")
    list_filter = ("status", "ref_year", "destination")
    search_fields = ("full_name", "email", "phone", "trip_title")
    readonly_fields = ("ref", "token", "travelers_label", "deposit_amount",
                       "created_at", "updated_at", "view_link")
    autocomplete_fields = ("destination", "linked_proposal")
    list_editable = ("status",)
    actions = ["mark_quoted", "mark_confirmed", "mark_paid"]
    fieldsets = (
        ("Reference", {"fields": ("ref", "status", "view_link")}),
        ("Client", {"fields": ("full_name", "email", "phone")}),
        ("Trip", {"fields": ("destination", "trip_title", ("num_adults", "num_children"),
                             ("start_date", "end_date"), "flexible_dates", "message")}),
        ("Quote & payment", {"fields": (("quoted_total", "currency_symbol"), "deposit_amount",
                                        "payment_reference", "payment_proof")}),
        ("Internal", {"fields": ("linked_proposal", "staff_notes", "created_at", "updated_at")}),
    )

    @admin.display(description="Status page")
    def view_link(self, obj):
        if obj.pk:
            url = reverse("booking_status", args=[obj.token])
            return format_html('<a href="{}" target="_blank">open client view</a>', url)
        return "—"

    @admin.action(description="Mark as quote sent")
    def mark_quoted(self, request, queryset):
        queryset.update(status="quoted")

    @admin.action(description="Mark as confirmed")
    def mark_confirmed(self, request, queryset):
        queryset.update(status="confirmed")

    @admin.action(description="Mark as paid in full")
    def mark_paid(self, request, queryset):
        queryset.update(status="paid")


class PackageDayInline(admin.TabularInline):
    model = models.PackageDay
    extra = 1
    fields = ("order", "day_label", "title", "description", "accommodation", "accommodation_note", "meals")


class PackageRateInline(admin.TabularInline):
    model = models.PackageRate
    extra = 1
    fields = ("order", "duration_label", "price_single", "price_double", "price_family")


@admin.register(models.Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "tag", "region", "duration_days",
                    "pricing_mode", "price_from", "is_featured", "is_active", "order")
    list_editable = ("is_featured", "is_active", "order")
    list_filter = ("kind", "tag", "pricing_mode", "is_active", "is_featured")
    search_fields = ("title", "region", "country")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("destination", "hero_image")
    filter_horizontal = ("gallery",)
    inlines = [PackageDayInline, PackageRateInline]
    fieldsets = (
        (None, {"fields": ("title", "slug", ("kind", "tag"), "summary",
                           ("region", "country"), "destination")}),
        ("Pricing", {"fields": (("pricing_mode", "price_from", "currency_symbol"),)}),
        ("Overview", {"fields": ("body", "highlights", ("duration_days",))}),
        ("Tour features", {"fields": (("tour_class", "accommodation_type"),
                                      ("is_private", "can_start_any_day", "can_customize"),
                                      "age_suitability")}),
        ("Route & logistics", {"fields": (("start_point", "end_point"),
                                          "activities", "transport", "getting_there")}),
        ("Inclusions", {"fields": ("included", "excluded")}),
        ("Media", {"fields": ("hero_image", "gallery", "video_url")}),
        ("Display", {"fields": (("is_featured", "is_active", "order"),)}),
    )


@admin.register(models.JournalPost)
class JournalPostAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "published", "published_at")
    list_editable = ("published",)
    list_filter = ("category", "published")
    search_fields = ("title", "excerpt", "body")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("cover_image",)
    fields = ("title", "slug", "category", "cover_image", "excerpt", "body",
              "author", ("published", "published_at"))


@admin.register(models.Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("author_name", "location", "rating", "trip", "approved", "created_at")
    list_editable = ("approved",)
    list_filter = ("approved", "rating")
    search_fields = ("author_name", "body", "trip")


@admin.register(models.FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "order")
    list_editable = ("order",)
    search_fields = ("question", "answer")


@admin.register(models.NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "created_at")
    search_fields = ("email",)
    readonly_fields = ("created_at",)


@admin.register(models.HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = ("__str__", "is_active", "order")
    list_editable = ("is_active", "order")
    fields = ("image", "caption", "is_active", "order")
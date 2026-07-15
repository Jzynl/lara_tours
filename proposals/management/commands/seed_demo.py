"""
Seed the database with a company profile, an agent, a destination and a sample
proposal so the app is usable immediately after `migrate`.

    python manage.py seed_demo

Re-running is safe; it won't duplicate the company profile or the sample proposal.
"""
import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand

from proposals.models import (
    Agent, CompanyProfile, Day, Destination, Hotel, PricingItem, Proposal,
)


class Command(BaseCommand):
    help = "Create demo company profile, catalog and a sample proposal."

    def handle(self, *args, **options):
        company = CompanyProfile.get_solo()
        company.name = "Lara Tours and Travels"
        company.tagline = "Unforgettable Experience"
        company.email = "info@laratoursandtravels.com"
        company.phone = "+255 782 206 905"
        company.whatsapp = "+255 782 206 905"
        company.website = "www.laratoursandtravels.com"
        company.address = "Sokoine Rd, Arusha"
        company.country = "Tanzania"
        company.about_us = (
            "Lara Tours was founded by a group of passionate Tanzanian travel "
            "enthusiasts who wanted to share the beauty of their homeland with the "
            "world.\n\n"
            "Today we craft authentic, personalised journeys across East Africa and "
            "beyond, never losing sight of our original mission: responsible, "
            "memorable travel."
        )
        company.closing_quote = "Wherever you go becomes a part of you somehow"
        company.closing_quote_author = "Anita Desai"
        company.primary_color = "#2f4d1e"
        company.accent_color = "#e8771c"
        company.payment_provider = "Selcom Lipa Namba"
        company.lipa_namba = "12345678"
        company.deposit_percent = 40
        company.default_included = (
            "All activities unless marked optional\n"
            "Meals as specified in the day-by-day section\n"
            "Taxes / VAT\n"
            "Hotel pickup and drop-off"
        )
        company.default_excluded = (
            "International flights\n"
            "Personal items and travel insurance\n"
            "Tips (guideline US$10 pp per day)\n"
            "Visa fees"
        )
        company.default_payment_terms = "40% payable 10 days before the trip and 60% on the day of travel."
        company.save()
        self.stdout.write(self.style.SUCCESS("✓ Company profile ready"))

        agent, _ = Agent.objects.get_or_create(
            name="Suzan Leon",
            defaults={"title": "Travel Consultant",
                      "email": "info@laratoursandtravels.com",
                      "phone": "+255 782 206 905"},
        )

        zanzibar, _ = Destination.objects.get_or_create(
            name="Stone Town",
            defaults={"region": "Zanzibar", "country": "Tanzania",
                      "description": "A UNESCO old town where Swahili, Arab and Indian "
                                     "worlds meet in carved doors and spice-scented lanes."},
        )
        nungwi, _ = Destination.objects.get_or_create(
            name="Nungwi Beach",
            defaults={"region": "Zanzibar", "country": "Tanzania",
                      "description": "Powder-white sand and turquoise water on Zanzibar's "
                                     "northern tip — dhows, sunsets and warm Indian Ocean swims."},
        )
        hotel, _ = Hotel.objects.get_or_create(
            name="The Mora",
            defaults={"hotel_type": "Hotel", "location": "Zanzibar",
                      "destination": zanzibar},
        )

        if Proposal.objects.filter(title="Creating Memories in Zanzibar").exists():
            self.stdout.write("Sample proposal already exists — skipping.")
            return

        proposal = Proposal.objects.create(
            title="Creating Memories in Zanzibar",
            cover_eyebrow="Creating memories in",
            client_title="Mr.",
            client_name="& Mrs. Hassan",
            num_adults=2,
            num_children=2,
            start_date=datetime.date(2026, 7, 4),
            end_date=datetime.date(2026, 7, 6),
            start_destination=zanzibar,
            end_destination=nungwi,
            agent=agent,
            status="draft",
        )

        Day.objects.create(
            proposal=proposal, day_number=1, day_type="arrival", destination=zanzibar,
            narrative="This is where it all begins. Wander the spice-scented lanes of a "
                      "UNESCO old town before settling into island life. After we greet "
                      "you and answer any questions, we'll show you Zanzibar's magic.",
            hotel=hotel, room_config="2× Deluxe Room",
            accommodation_blurb="When you stay at The Mora, you're perfectly placed to "
                                "enjoy this leg of your journey.",
            meal_lunch=True, meal_dinner=True,
        )
        Day.objects.create(
            proposal=proposal, day_number=2, day_type="standard", destination=nungwi,
            narrative="Trade the old town for the coast. Swim in warm turquoise water, "
                      "laze under palms and watch the dhows drift home at sunset.",
            hotel=hotel, room_config="2× Deluxe Room",
            accommodation_blurb="Extend your stay at The Mora for another night.",
            meal_breakfast=True, meal_lunch=True, meal_dinner=True,
        )
        Day.objects.create(
            proposal=proposal, day_number=3, day_type="departure", destination=nungwi,
            narrative="Your Zanzibar escape comes to a close. We're sure you've had the "
                      "most wonderful time — until next time.",
            meal_breakfast=True,
        )

        PricingItem.objects.create(proposal=proposal, label="Adult", quantity=1,
                                    unit_cost=Decimal("400.00"), markup_pct=Decimal("20"), order=1)
        PricingItem.objects.create(proposal=proposal, label="Adult", quantity=1,
                                    unit_cost=Decimal("400.00"), markup_pct=Decimal("20"), order=2)
        PricingItem.objects.create(proposal=proposal, label="Child", quantity=2,
                                    unit_cost=Decimal("220.00"), markup_pct=Decimal("18"), order=3)

        self.stdout.write(self.style.SUCCESS(
            f"✓ Sample proposal created: {proposal.ref_number} (total {proposal.currency_symbol}{proposal.total})"
        ))
        self.stdout.write("Add atmospheric photos via the Image search page, then preview the PDF.")

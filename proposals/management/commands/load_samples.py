"""
Load several complete sample proposals so you can see the tool in action —
multiple destinations, hotels, agents, full day-by-day plans and pricing.

It also tries to pull a few atmospheric photos per destination from Openverse
(no API key needed) so the previews and PDFs look real. Photo fetching needs
internet; if it's unavailable the proposals are still created (just without
images).

    python manage.py load_samples
    python manage.py load_samples --no-images     # skip photo fetching (faster)

Safe to re-run: existing destinations/proposals are reused, not duplicated.
"""
import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand

from proposals import images as stock
from proposals.models import (
    Agent, CompanyProfile, Day, Destination, DestinationImage, Hotel,
    PricingItem, Proposal,
)


DESTINATIONS = {
    "Stone Town": ("Zanzibar", "Tanzania",
                   "A UNESCO old town where Swahili, Arab and Indian worlds meet in carved "
                   "doors, spice markets and call-to-prayer at dusk.", "Stone Town Zanzibar"),
    "Nungwi Beach": ("Zanzibar", "Tanzania",
                     "Powder-white sand and turquoise water on Zanzibar's northern tip — "
                     "dhows, sunsets and warm Indian Ocean swims.", "Nungwi beach Zanzibar"),
    "Ubud": ("Bali", "Indonesia",
             "Bali's green heart: emerald rice terraces, river gorges, temples and a slow, "
             "spiritual rhythm.", "Ubud Bali rice terrace"),
    "Seminyak": ("Bali", "Indonesia",
                 "Stylish beach clubs, sunset surf and golden sand on Bali's chic "
                 "south-west coast.", "Seminyak Bali beach sunset"),
    "Dubai": ("Dubai", "United Arab Emirates",
              "Where desert meets future — soaring towers, golden dunes, souks and "
              "the glittering Marina.", "Dubai skyline marina"),
    "Serengeti": ("Arusha", "Tanzania",
                  "Endless golden plains and the thunder of the great migration — the "
                  "safari of a lifetime.", "Serengeti savanna wildlife"),
}

# title, eyebrow, client_title, client_name, adults, children, start, days,
#   start_dest, end_dest, [ (day_type, dest, narrative, hotel, rooms, b,l,d) ],
#   [ (label, qty, cost, markup) ]
def _d(y, m, d):
    return datetime.date(y, m, d)


class Command(BaseCommand):
    help = "Load sample destinations, hotels, agents and full proposals (with photos)."

    def add_arguments(self, parser):
        parser.add_argument("--no-images", action="store_true",
                            help="Skip fetching photos from Openverse.")

    def handle(self, *args, **options):
        self._ensure_company()
        agents = self._ensure_agents()
        dests = self._ensure_destinations(fetch=not options["no_images"])
        self._ensure_hotels(dests)
        self._build_proposals(dests, agents)
        self.stdout.write(self.style.SUCCESS(
            "\nDone. Open the Proposals page to browse and preview them."
        ))

    # ------------------------------------------------------------------
    def _ensure_company(self):
        c = CompanyProfile.get_solo()
        if not c.name or c.name == "Lara Tours and Travels" and not c.email:
            pass
        c.name = c.name or "Lara Tours and Travels"
        c.tagline = c.tagline or "Unforgettable Experience"
        c.email = c.email or "info@laratoursandtravels.com"
        c.phone = c.phone or "+255 782 206 905"
        c.whatsapp = c.whatsapp or "+255 782 206 905"
        c.website = c.website or "www.laratoursandtravels.com"
        c.address = c.address or "Sokoine Rd, Arusha"
        c.country = c.country or "Tanzania"
        c.primary_color = "#2f4d1e"
        c.accent_color = "#e8771c"
        c.about_us = c.about_us or (
            "Lara Tours was founded by passionate Tanzanian travel enthusiasts who wanted "
            "to share the beauty of their homeland — and the world — with every traveller.\n\n"
            "Today we craft authentic, personalised journeys across East Africa, the Indian "
            "Ocean isles and beyond."
        )
        c.closing_quote = c.closing_quote or "Wherever you go becomes a part of you somehow"
        c.closing_quote_author = c.closing_quote_author or "Anita Desai"
        c.default_included = c.default_included or (
            "All activities unless marked optional\nMeals as specified\nTaxes / VAT\n"
            "Airport / hotel transfers"
        )
        c.default_excluded = c.default_excluded or (
            "International flights\nPersonal items and travel insurance\n"
            "Tips (guideline US$10 pp per day)\nVisa fees"
        )
        c.default_payment_terms = c.default_payment_terms or (
            "40% payable 10 days before the trip and 60% on the day of travel."
        )
        c.save()
        self.stdout.write("✓ Company profile ready")

    def _ensure_agents(self):
        a1, _ = Agent.objects.get_or_create(name="Suzan Leon", defaults={
            "title": "Senior Travel Consultant", "email": "suzan@laratoursandtravels.com",
            "phone": "+255 782 206 905"})
        a2, _ = Agent.objects.get_or_create(name="David Mushi", defaults={
            "title": "Travel Consultant", "email": "david@laratoursandtravels.com",
            "phone": "+255 782 206 906"})
        return [a1, a2]

    def _ensure_destinations(self, fetch):
        out = {}
        for name, (region, country, desc, query) in DESTINATIONS.items():
            dest, _ = Destination.objects.get_or_create(
                name=name, defaults={"region": region, "country": country, "description": desc})
            out[name] = dest
            if fetch and dest.images.count() < 2:
                self.stdout.write(f"  fetching photos for {name}…", ending="")
                self.stdout.flush()
                added = self._fetch_images(dest, query, count=3)
                self.stdout.write(self.style.SUCCESS(f" {added} added") if added
                                  else self.style.WARNING(" none (offline?)"))
        self.stdout.write("✓ Destinations ready")
        return out

    def _fetch_images(self, dest, query, count=3):
        try:
            results = stock.search(query, source="openverse", per_page=count + 4)
        except Exception:
            results = []
        added = 0
        for r in results:
            if added >= count:
                break
            img = stock.import_photo(
                source_id=r["id"], full_url=r["full"], photographer=r["photographer"],
                photographer_url=r["photographer_url"], title=r["alt"], category="destination",
            )
            if img:
                DestinationImage.objects.create(
                    destination=dest, image=img,
                    order=dest.destinationimage_set.count())
                added += 1
        return added

    def _ensure_hotels(self, dests):
        specs = [
            ("The Mora", "Hotel", "Zanzibar", "Stone Town"),
            ("Nungwi Dreams Resort", "Resort", "Nungwi", "Nungwi Beach"),
            ("Ubud Jungle Retreat", "Villa", "Ubud", "Ubud"),
            ("Seminyak Beach House", "Hotel", "Seminyak", "Seminyak"),
            ("Marina Sky Hotel", "Hotel", "Dubai Marina", "Dubai"),
            ("Serengeti Tented Camp", "Camp", "Serengeti", "Serengeti"),
        ]
        for name, kind, loc, dest_name in specs:
            Hotel.objects.get_or_create(name=name, defaults={
                "hotel_type": kind, "location": loc, "destination": dests.get(dest_name)})

    # ------------------------------------------------------------------
    def _build_proposals(self, dests, agents):
        hotel = {h.name: h for h in Hotel.objects.all()}
        plans = [
            dict(title="Creating Memories in Zanzibar", eyebrow="Creating memories in",
                 ct="Mr.", cn="& Mrs. Hassan", ad=2, ch=2, start=_d(2026, 7, 4),
                 start_dest="Stone Town", end_dest="Nungwi Beach", agent=agents[0],
                 days=[("arrival", "Stone Town",
                        "This is where it all begins — spice-scented lanes, carved doors and "
                        "the warm welcome of the isles.", "The Mora", "2× Deluxe Room", 0, 1, 1),
                       ("standard", "Nungwi Beach",
                        "Trade the old town for the coast — turquoise water, palms and dhows "
                        "drifting home at sunset.", "Nungwi Dreams Resort", "2× Sea-View Room",
                        1, 1, 1),
                       ("departure", "Nungwi Beach",
                        "Your Zanzibar escape comes to a close. Until next time.", "", "", 1, 0, 0)],
                 price=[("Adult", 1, "400", "20"), ("Adult", 1, "400", "20"),
                        ("Child", 2, "220", "18")]),
            dict(title="Bali Honeymoon Escape", eyebrow="Creating memories in",
                 ct="Mr.", cn="& Mrs. Okello", ad=2, ch=0, start=_d(2026, 8, 12),
                 start_dest="Ubud", end_dest="Seminyak", agent=agents[1],
                 days=[("arrival", "Ubud",
                        "Begin in Bali's green heart — rice terraces, temples and a slow, "
                        "romantic rhythm.", "Ubud Jungle Retreat", "1× Pool Villa", 0, 1, 1),
                       ("standard", "Ubud",
                        "A day among the terraces and waterfalls, ending with a private "
                        "candlelit dinner.", "Ubud Jungle Retreat", "1× Pool Villa", 1, 1, 1),
                       ("standard", "Seminyak",
                        "Down to the coast for beach clubs, sunset surf and golden sand.",
                        "Seminyak Beach House", "1× Ocean Suite", 1, 1, 0),
                       ("departure", "Seminyak",
                        "Farewell to the island of the gods, hearts full.", "", "", 1, 0, 0)],
                 price=[("Adult", 2, "780", "22")]),
            dict(title="Dubai City & Desert", eyebrow="Creating memories in",
                 ct="Ms.", cn="Amina Said", ad=3, ch=1, start=_d(2026, 9, 2),
                 start_dest="Dubai", end_dest="Dubai", agent=agents[0],
                 days=[("arrival", "Dubai",
                        "Arrive where desert meets the future — towers, souks and the "
                        "glittering Marina.", "Marina Sky Hotel", "2× Family Room", 0, 0, 1),
                       ("standard", "Dubai",
                        "City icons by day, then a golden-dune safari with dinner under "
                        "the stars.", "Marina Sky Hotel", "2× Family Room", 1, 0, 1),
                       ("departure", "Dubai",
                        "One last skyline view before your onward journey.", "", "", 1, 0, 0)],
                 price=[("Adult", 3, "520", "25"), ("Child", 1, "300", "20")]),
        ]

        for p in plans:
            if Proposal.objects.filter(title=p["title"]).exists():
                self.stdout.write(f"  · {p['title']} already exists — skipping")
                continue
            n_days = len(p["days"])
            sd = dests.get(p["start_dest"])
            proposal = Proposal.objects.create(
                title=p["title"], cover_eyebrow=p["eyebrow"],
                client_title=p["ct"], client_name=p["cn"],
                num_adults=p["ad"], num_children=p["ch"],
                start_date=p["start"], end_date=p["start"] + datetime.timedelta(days=n_days - 1),
                start_destination=sd, end_destination=dests.get(p["end_dest"]),
                agent=p["agent"], status="draft",
                cover_image=(sd.ordered_images()[0] if sd and sd.ordered_images() else None),
            )
            for i, (dtype, dname, narr, hname, rooms, b, l, dn) in enumerate(p["days"], start=1):
                Day.objects.create(
                    proposal=proposal, day_number=i, day_type=dtype,
                    destination=dests.get(dname), narrative=narr,
                    hotel=hotel.get(hname) if hname else None, room_config=rooms,
                    accommodation_blurb=("When you stay at %s, you're perfectly placed to "
                                         "enjoy this leg of your journey." % hname) if hname else "",
                    meal_breakfast=bool(b), meal_lunch=bool(l), meal_dinner=bool(dn))
            for order, (label, qty, cost, markup) in enumerate(p["price"], start=1):
                PricingItem.objects.create(
                    proposal=proposal, label=label, quantity=qty,
                    unit_cost=Decimal(cost), markup_pct=Decimal(markup), order=order)
            self.stdout.write(self.style.SUCCESS(
                f"  ✓ {proposal.ref_number}  {p['title']}  "
                f"({proposal.currency_symbol}{proposal.total})"))

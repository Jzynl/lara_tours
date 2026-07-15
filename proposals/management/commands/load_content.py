"""
Seed the marketing site with real, detailed content:
 - detailed tour packages (day-by-day, rate grids, inclusions, getting there)
 - fixed-price local experiences
 - journal posts, reviews and FAQs

    python manage.py load_content

Safe to re-run. Run load_destinations --with-images first for cover photos.
"""
import datetime
from decimal import Decimal as D

from django.core.management.base import BaseCommand

from proposals.models import (Destination, FAQ, JournalPost, Package, PackageDay,
                              PackageRate, Review)


def hero_for(name_or_region):
    d = (Destination.objects.filter(name=name_or_region).first()
         or Destination.objects.filter(region=name_or_region).first())
    img = None
    if d:
        imgs = d.ordered_images()
        img = imgs[0] if imgs else None
    return d, img


class Command(BaseCommand):
    help = "Load detailed packages, experiences, posts, reviews and FAQs."

    def handle(self, *args, **options):
        self._tours()
        self._experiences()
        self._posts()
        self._reviews()
        self._faqs()
        self.stdout.write(self.style.SUCCESS("\nDone. Open a package page to see the tabs."))

    # ------------------------------------------------------------------
    def _mk(self, **kw):
        days = kw.pop("days", [])
        rates = kw.pop("rates", [])
        title = kw["title"]
        if Package.objects.filter(title=title).exists():
            self.stdout.write(f"  · {title} exists — skipping")
            return
        d, hero = hero_for(kw.pop("dest", kw.get("region", "")))
        pkg = Package.objects.create(destination=d, hero_image=hero, **kw)
        if d:
            for img in d.ordered_images()[:5]:
                pkg.gallery.add(img)
        for i, (label, title_, desc, acc, note, meals) in enumerate(days):
            PackageDay.objects.create(package=pkg, order=i, day_label=label, title=title_,
                                      description=desc, accommodation=acc,
                                      accommodation_note=note, meals=meals)
        for i, (dur, s, db, fam) in enumerate(rates):
            PackageRate.objects.create(package=pkg, order=i, duration_label=dur,
                                       price_single=s and D(str(s)), price_double=db and D(str(db)),
                                       price_family=fam and D(str(fam)))
        self.stdout.write(self.style.SUCCESS(f"  ✓ {pkg.title}"))

    def _tours(self):
        self._mk(
            title="Mikumi Train Safari", kind="tour", tag="Safari", pricing_mode="from",
            price_from=None, region="Mikumi", dest="Mikumi", duration_days=2,
            tour_class="midrange", accommodation_type="Lodge", start_point="Dar es Salaam",
            end_point="Dar es Salaam", activities="Game drives", transport="SGR train & road; open 4x4",
            is_featured=True, order=0,
            summary="Ride the SGR train to Mikumi for game drives, waterfalls and a Maasai village.",
            body="An easy, affordable escape from Dar es Salaam by SGR train. Enjoy game drives among "
                 "elephants, giraffes and lions on the Mkata plains, a guided waterfall walk, and a "
                 "visit to a Maasai village — a great first safari or group getaway.",
            highlights="SGR train journey\nMikumi game drives\nWaterfall walk\nMaasai village visit\nGroup entertainment",
            included="Return SGR train\nPark & conservation fees\nGame drives in open 4x4\nLodge accommodation\nMeals as specified\nEnglish-speaking guide",
            excluded="Drinks & personal items\nTips (≈US$10 pp/day)\nTravel insurance\nOptional activities",
            getting_there="Starts and ends in Dar es Salaam. Travel by SGR train to Morogoro, then "
                          "private vehicle into the park. Airport transfers in Dar can be arranged.",
            days=[
                ("Day 1", "Dar → Mikumi", "SGR train to Morogoro, transfer into Mikumi, lunch in the park and an afternoon game drive.",
                 "Lodge near Mikumi", "Mid-range lodge", "Lunch & dinner"),
                ("Day 2", "Waterfalls & village", "Morning waterfall walk, afternoon Maasai village visit, then evening SGR train back to Dar.",
                 "End of tour", "", "Breakfast & lunch"),
            ],
            rates=[
                ("1 night / day trip", "310.50", "442.75", "644"),
                ("2 nights / 3 days", "621", "885.50", "1288"),
                ("3 nights / 4 days", "931.50", "1328.25", "1932"),
                ("4 nights / 5 days", "1242", "1771", "1932"),
            ],
        )
        self._mk(
            title="Northern Circuit Safari", kind="tour", tag="Safari", pricing_mode="from",
            price_from=None, region="Northern Circuit", dest="Serengeti", duration_days=4,
            tour_class="midrange", accommodation_type="Lodge", start_point="Arusha",
            end_point="Arusha", activities="Game drives", transport="4x4 safari vehicle",
            is_featured=True, order=1,
            summary="Tanzania's classic circuit — Tarangire, Serengeti, Ngorongoro and Manyara.",
            body="The definitive Tanzanian safari across the great northern parks: elephant herds at "
                 "Tarangire, the endless Serengeti plains, the wildlife-packed Ngorongoro Crater and the "
                 "tree-climbing lions of Lake Manyara.",
            highlights="Serengeti plains\nNgorongoro Crater\nTarangire elephants\nLake Manyara\nBig Five",
            included="Park & crater fees\nGame drives in 4x4\nLodge accommodation\nMeals as specified\nProfessional guide",
            excluded="International & domestic flights\nVisas & insurance\nDrinks\nTips",
            getting_there="Starts and ends in Arusha (Kilimanjaro Airport, JRO). Airport transfers can be arranged.",
            days=[
                ("Day 1", "Arusha → Tarangire", "Morning drive to Tarangire for an afternoon game drive among the baobabs and elephants.", "Lodge", "Mid-range lodge", "All meals"),
                ("Day 2", "Serengeti", "Full day exploring the endless Serengeti plains.", "Lodge", "Mid-range lodge", "All meals"),
                ("Day 3", "Ngorongoro Crater", "Descend into the crater for one of Africa's greatest wildlife spectacles.", "Lodge", "Crater-rim lodge", "All meals"),
                ("Day 4", "Manyara → Arusha", "Lake Manyara game drive, then return to Arusha.", "End of tour", "", "Breakfast & lunch"),
            ],
            rates=[
                ("1 night / day trip", "545.10", "608", "836"),
                ("2 nights / 3 days", "1090.20", "1216", "1672"),
                ("3 nights / 4 days", "1635.30", "1824", "2508"),
                ("4 nights / 5 days", "2180.40", "2432", "2508"),
            ],
        )
        self._mk(
            title="3-Day Zanzibar to Nyerere Fly-in Safari", kind="tour", tag="Safari", pricing_mode="from",
            price_from=None, region="Nyerere", dest="Nyerere NP", duration_days=3,
            tour_class="midrange", accommodation_type="Lodge", start_point="Zanzibar",
            end_point="Zanzibar", activities="Game drives, walking safari & boat trip",
            transport="Air transfer; open-sided 4x4", is_featured=True, order=2,
            age_suitability="Minimum age 2 years",
            summary="A fast, action-packed fly-in from the coast — full-day safari, a Maasai visit and a Rufiji sunset cruise.",
            body="Big wildlife and real culture in just three days. Fly from Zanzibar straight into Nyerere "
                 "National Park for a full day on safari, then a bush walk, a visit with a Maasai community "
                 "and a sunset boat cruise on the Rufiji River — before flying back to the beach.",
            highlights="Scenic flights from Zanzibar\nFull-day game drive\nRufiji sunset boat safari\nMaasai & village visit\nGuided bush walk",
            included="Return flights Zanzibar \u21c4 Nyerere\nPark & conservation fees\nAirport & airstrip transfers\nLodge accommodation\nAll meals as specified\nGame drives, walk & boat safari\nEnglish-speaking guide",
            excluded="International flights\nVisas & travel insurance\nDrinks & personal items\nTips",
            getting_there="Starts and ends in Zanzibar. Light-aircraft transfer to the park airstrip; airport "
                          "transfers included. Minimum age 2 years. Additional nights are not arranged on this trip.",
            days=[
                ("Day 1", "Zanzibar \u2192 Nyerere NP", "Morning flight to the park, then straight into a full-day game drive.", "Selous-area Safari Lodge", "Mid-range lodge near Nyerere NP", "All meals"),
                ("Day 2", "Bush walk, culture & boat safari", "A morning bush walk, a Maasai and local-village visit, and an evening sunset boat safari on the Rufiji River.", "Selous-area Safari Lodge", "Mid-range lodge", "All meals"),
                ("Day 3", "Nyerere NP \u2192 Zanzibar", "An early flight back to Zanzibar and a transfer to your hotel.", "End of tour", "", "Breakfast"),
            ],
        )
        self._mk(
            title="4-Day Zanzibar & Nyerere Safari", kind="tour", tag="Safari", pricing_mode="from",
            price_from=None, region="Nyerere", dest="Nyerere NP", duration_days=4,
            tour_class="midrange", accommodation_type="Lodge", start_point="Zanzibar",
            end_point="Zanzibar", activities="Game drives, walking safari & boat trip",
            transport="Air transfer; open-sided 4x4 & minivan", is_featured=False, order=3,
            summary="A longer fly-in safari — more time for game drives, a walking safari and the Rufiji River.",
            body="Trade the beaches of Zanzibar for the wild heart of southern Tanzania. Fly into Nyerere "
                 "National Park for four unhurried days of game drives, a guided walking safari with an armed "
                 "ranger, and a boat cruise on the Rufiji — prime territory for elephants, hippos and the rare "
                 "African wild dog — before returning to the coast.",
            highlights="Scenic flights from Zanzibar\nRufiji River boat safari\nGuided walking safari\nElephants, hippos & wild dog\nThree nights in the bush",
            included="Return flights Zanzibar \u21c4 Nyerere\nPark & conservation fees\nAirport & airstrip transfers\nLodge accommodation\nMeals as specified\nGame drives, walk & boat safari\nEnglish-speaking guide",
            excluded="International flights\nVisas & travel insurance\nDrinks & personal items\nTips",
            getting_there="Starts and ends in Zanzibar. Light-aircraft transfer to the park airstrip; airport "
                          "transfers included. Extra nights before or after the safari can be arranged for an extra cost.",
            days=[
                ("Day 1", "Zanzibar \u2192 Nyerere NP", "Fly to the park, transfer to your lodge, and enjoy an afternoon game drive.", "Selous-area Safari Lodge", "Mid-range lodge near Nyerere NP", "Lunch & dinner"),
                ("Day 2", "Game drives & boat safari", "A full day of game drives and an afternoon boat safari on the Rufiji River.", "Selous-area Safari Lodge", "Mid-range lodge", "All meals"),
                ("Day 3", "Walking safari", "Morning game drive and a guided walking safari with an armed ranger.", "Selous-area Safari Lodge", "Mid-range lodge", "All meals"),
                ("Day 4", "Nyerere NP \u2192 Zanzibar", "A final morning drive, then fly back to Zanzibar.", "End of tour", "", "Breakfast"),
            ],
        )
        self._mk(
            title="3-Day Nyerere Fly-in with 2 Game Drives", kind="tour", tag="Safari", pricing_mode="from",
            price_from=None, region="Nyerere", dest="Nyerere NP", duration_days=3,
            tour_class="midrange", accommodation_type="Lodge", start_point="Zanzibar",
            end_point="Zanzibar", activities="Game drives & boat trip",
            transport="Air transfer; open-sided 4x4", is_featured=False, order=4,
            summary="A short, big-game escape — two full game drives and a Rufiji boat safari, all from Zanzibar.",
            body="A compact fly-in safari built around the wildlife. Fly from Zanzibar into Nyerere National "
                 "Park for two rewarding game drives and a boat safari on the Rufiji River, led by a professional "
                 "guide, with comfortable lodge nights and time to relax between adventures — then fly back to the coast.",
            highlights="Scenic flights from Zanzibar\nTwo full game drives\nRufiji River boat safari\nProfessional safari guide\nComfortable lodge stay",
            included="Return flights Zanzibar \u21c4 Nyerere\nPark & conservation fees\nAirport & airstrip transfers\nLodge accommodation\nAll meals as specified\nGame drives & boat safari\nEnglish-speaking guide",
            excluded="International flights\nVisas & travel insurance\nDrinks & personal items\nTips",
            getting_there="Starts and ends in Zanzibar. Light-aircraft transfer to the park airstrip; airport "
                          "transfers included. Extra nights before or after the safari can be arranged for an extra cost.",
            days=[
                ("Day 1", "Zanzibar \u2192 Nyerere NP", "Fly to the park, settle into your lodge, and head out on an afternoon game drive.", "Selous-area Safari Lodge", "Mid-range lodge near Nyerere NP", "All meals"),
                ("Day 2", "Game drive & boat safari", "A morning game drive and an afternoon boat safari on the Rufiji River.", "Selous-area Safari Lodge", "Mid-range lodge", "All meals"),
                ("Day 3", "Nyerere NP \u2192 Zanzibar", "A morning flight back to Zanzibar and transfer to your hotel.", "End of tour", "", "Breakfast"),
            ],
        )

    def _experiences(self):
        exps = [
            ("Dar Local Cooking Class", "45", "Cultural",
             "Cook — and feast on — authentic Swahili dishes with a local family in Dar es Salaam.",
             "Shop for spices at a local market, then learn to prepare classic coastal dishes — pilau, "
             "coconut curry and chapati — before sitting down to enjoy the feast you've made."),
            ("Tie & Dye Making Workshop", "35", "Cultural",
             "Make your own vibrant kanga-style fabric in a hands-on tie & dye workshop.",
             "A colourful, hands-on afternoon learning traditional tie & dye techniques — fold, bind and "
             "dye your own fabric to take home as a one-of-a-kind souvenir."),
            ("Village & Culture Experience", "40", "Cultural",
             "Spend a day with a local community — traditions, dance, food and everyday life.",
             "Step into local life: traditional dances, a lifestyle explanation, crafts and a shared meal "
             "— a warm, authentic cultural exchange."),
            ("Farm Visit & Tasting", "30", "Local",
             "Tour a working farm and taste tropical fruits and spices straight from the source.",
             "Walk a working farm, learn how spices and tropical fruits are grown, and taste them fresh — "
             "a relaxed, delicious morning out."),
            ("Guided Nature Hike", "35", "Adventure",
             "A guided half-day hike through forest and hills with a local guide.",
             "Lace up for a scenic guided hike — forest trails, viewpoints and birdlife, at a relaxed pace "
             "with a knowledgeable local guide."),
        ]
        for i, (title, price, tag, summary, body) in enumerate(exps):
            if Package.objects.filter(title=title).exists():
                continue
            _, hero = hero_for("Stone Town")
            Package.objects.create(
                title=title, kind="experience", pricing_mode="fixed", tag=tag,
                price_from=None, region="Dar es Salaam", country="Tanzania",
                duration_days=1, summary=summary, body=body, hero_image=hero,
                is_active=True, order=10 + i,
                included="Local guide / host\nAll materials or ingredients\nRefreshments",
            )
            self.stdout.write(self.style.SUCCESS(f"  ✓ experience: {title} (${price})"))

    def _posts(self):
        data = [
            ("Best time to visit Zanzibar", "Guides", "Nungwi Beach",
             "Sun, sea and when to go — a month-by-month guide to the Spice Island.",
             "Zanzibar is a year-round destination, but the dry seasons (June–October and December–"
             "February) bring the clearest skies and calmest seas. The long rains (March–May) are "
             "quieter and greener, with lower prices. Whenever you go, the water stays warm."),
            ("Mikumi by train: the easy safari", "Guides", "Mikumi",
             "Why the SGR train makes Mikumi the perfect weekend safari from Dar es Salaam.",
             "Just a few hours from Dar by the smooth new SGR train, Mikumi packs elephants, lions and "
             "giraffes into an easy weekend — no long drives, no flights, and gentle on the budget."),
            ("What to pack for an African safari", "Guides", "Serengeti",
             "Neutral colours, layers and a good camera — your safari packing essentials.",
             "Pack light in soft neutral tones — khaki and beige blend into the bush. Mornings are cold "
             "and middays hot, so layers matter. Bring binoculars, sunscreen, a hat and spare memory cards."),
        ]
        for j, (title, cat, dest, excerpt, body) in enumerate(data):
            if JournalPost.objects.filter(title=title).exists():
                continue
            _, cover = hero_for(dest)
            JournalPost.objects.create(title=title, category=cat, excerpt=excerpt, body=body,
                                       cover_image=cover, author="Lara Tours", published=True,
                                       published_at=datetime.date.today() - datetime.timedelta(days=7 * j))
            self.stdout.write(self.style.SUCCESS(f"  ✓ post: {title}"))

    def _reviews(self):
        data = [
            ("Amani K.", "Nairobi, Kenya", 5, "Mikumi Train Safari",
             "The train journey was so smooth and Mikumi was full of animals. Lara organised everything "
             "perfectly — a fantastic weekend."),
            ("The Okello Family", "Kampala, Uganda", 5, "Northern Circuit Safari",
             "We saw all of the Big Five! Our guide was incredible and the lodges were wonderful. "
             "Worth every dollar."),
            ("Sara & Tom", "London, UK", 5, "Zanzibar to Nyerere Fly-in Safari",
             "Beach one day, big game the next — the fly-in safari was seamless and the boat safari on "
             "the Rufiji was unforgettable."),
        ]
        for name, loc, rating, trip, body in data:
            if Review.objects.filter(author_name=name, trip=trip).exists():
                continue
            Review.objects.create(author_name=name, location=loc, rating=rating, trip=trip,
                                  body=body, approved=True)
            self.stdout.write(self.style.SUCCESS(f"  ✓ review: {name}"))

    def _faqs(self):
        data = [
            ("Why is the price shown as 'from'?",
             "Safari and travel rates change with the season and with flight prices, so we show a "
             "starting price. Your agent confirms the exact figure for your chosen dates before you pay."),
            ("Do I pay a deposit to confirm?",
             "Yes — once you accept your quote, a deposit (usually 40%) confirms your booking, with the "
             "balance due before travel. Local experiences can be booked at their fixed price."),
            ("Can you customise any itinerary?",
             "Absolutely — tell us your dates, budget and dreams and we'll tailor everything to you."),
            ("What board options are there?",
             "Bed & Breakfast, Half Board, Full Board or All-Inclusive — you choose when you request "
             "your quote, and it's reflected in your price."),
            ("How do I pay?",
             "By mobile money or bank transfer to our Lipa Namba. We confirm your booking as soon as "
             "payment is received."),
            ("How do I book?",
             "Pick a trip, choose your dates and details, and hit Get a quote — it goes straight to our "
             "team on WhatsApp or email to sort out the rest."),
        ]
        for k, (q, a) in enumerate(data):
            if FAQ.objects.filter(question=q).exists():
                continue
            FAQ.objects.create(question=q, answer=a, order=k)
            self.stdout.write(self.style.SUCCESS(f"  ✓ faq: {q[:40]}…"))

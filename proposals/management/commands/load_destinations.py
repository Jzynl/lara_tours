"""
Load Lara Tours' destination catalog — region overviews and key landmarks —
each with a polished, reusable travel blurb.

    python manage.py load_destinations                 # text only (fast)
    python manage.py load_destinations --with-images   # also pull 2 photos each (slower, needs internet)

Safe to re-run: it refreshes the blurb on existing destinations and never
duplicates them.
"""
from django.core.management.base import BaseCommand

from proposals import images as stock
from proposals.models import Destination, DestinationImage


# (name, region, country, blurb)
DESTINATIONS = [
    # ---------------- BALI ----------------
    ("Bali", "Bali", "Indonesia",
     "The Island of the Gods wears a thousand shades of green. Temple smoke drifts over "
     "emerald rice terraces, surf curls against black-sand coves, and every village keeps "
     "its own rhythm of offerings and gamelan. Bali is equal parts adventure and serenity "
     "— a place that slows your pulse and lifts your spirit."),
    ("Ubud", "Bali", "Indonesia",
     "Bali's cultural heart, cradled in jungle and river gorge. Wander artisan markets and "
     "ancient temples, watch barong dancers at dusk, and breathe the cool green air of the "
     "rice terraces. Ubud is where the island feels most itself — creative, spiritual and unhurried."),
    ("Seminyak", "Bali", "Indonesia",
     "Bali at its most stylish: designer boutiques, beach clubs and long golden sunsets over "
     "the Indian Ocean. Days drift from poolside loungers to sundowner cocktails as the surf "
     "rolls in. Chic, social and effortlessly cool."),
    ("Uluwatu", "Bali", "Indonesia",
     "Perched on dramatic limestone cliffs at Bali's southern tip, Uluwatu pairs world-class "
     "surf with a sea temple suspended above the waves. Stay for the sunset Kecak fire dance, "
     "performed against a sky of molten orange — pure Balinese magic."),
    ("Tegalalang Rice Terraces", "Bali", "Indonesia",
     "Carved into the hillsides above Ubud, these emerald terraces ripple down the valley in "
     "the traditional subak irrigation pattern. Walk the narrow paths between paddies, swing "
     "out over the greenery, and watch farmers work as they have for centuries."),
    ("Nusa Penida", "Bali", "Indonesia",
     "A rugged island escape off Bali's coast, where cliffs plunge into impossibly turquoise "
     "water. Snorkel with manta rays, stand above the famous Kelingking cliff, and trade the "
     "crowds for raw, cinematic coastline."),

    # ---------------- BANGKOK ----------------
    ("Bangkok", "Bangkok", "Thailand",
     "Thailand's electric capital never sleeps. Golden temples and royal palaces sit beside "
     "steaming street-food stalls, neon night markets and sleek rooftop bars. Glide the canals "
     "by long-tail boat by day and lose yourself in the buzz by night — Bangkok is sensory "
     "overload in the best way."),
    ("Grand Palace", "Bangkok", "Thailand",
     "The dazzling heart of old Bangkok — a complex of gilded spires, mirrored mosaics and the "
     "revered Emerald Buddha. For over two centuries this was home to Thai kings, and it remains "
     "the country's most sacred and spectacular landmark."),
    ("Wat Arun", "Bangkok", "Thailand",
     "The Temple of Dawn rises from the Chao Phraya River in tiers of porcelain-studded spires. "
     "Climb its steep steps for sweeping river views, or admire it at sunset when the light turns "
     "it to gold."),
    ("Chatuchak Market", "Bangkok", "Thailand",
     "One of the world's largest weekend markets — thousands of stalls of crafts, vintage finds, "
     "street food and curiosities. A maze of colour, bargains and irresistible aromas where you "
     "could happily lose a whole day."),

    # ---------------- PHUKET ----------------
    ("Phuket", "Phuket", "Thailand",
     "Thailand's largest island and the gateway to the Andaman Sea. Powder-soft beaches and "
     "turquoise bays meet buzzing night markets and a charming old town of Sino-Portuguese "
     "shophouses. Island-hop to hidden lagoons by day, feast on fresh seafood by night."),
    ("Phi Phi Islands", "Phuket", "Thailand",
     "A cluster of jungle-clad limestone islands rising from glassy emerald water. Snorkel coral "
     "gardens, swim in sheltered lagoons and laze on beaches framed by towering cliffs — among "
     "the most beautiful seascapes in Asia."),
    ("Phuket Old Town", "Phuket", "Thailand",
     "Pastel Sino-Portuguese shophouses, hip cafés and lantern-lit lanes give Phuket Town its "
     "photogenic charm. Wander the heritage streets, sample Peranakan flavours and soak up a "
     "slower, storied side of the island."),
    ("Big Buddha", "Phuket", "Thailand",
     "Seated serenely atop Nakkerd Hill, the 45-metre marble Big Buddha watches over the island. "
     "The climb rewards you with panoramic views across Phuket's bays and a moment of calm above it all."),

    # ---------------- DUBAI ----------------
    ("Dubai", "Dubai", "United Arab Emirates",
     "Where the desert meets the future. Dubai dazzles with the world's tallest tower, "
     "palm-shaped islands and gold-filled souks, then softens into golden dunes just beyond the "
     "skyline. Brunch in the sky, shop the world, ride a camel at sunset — here, the "
     "extraordinary is everyday."),
    ("Burj Khalifa", "Dubai", "United Arab Emirates",
     "The tallest building on earth pierces the clouds at over 828 metres. Ride to the "
     "observation decks for a view that stretches from desert to sea, and watch the city glitter "
     "to life as the sun goes down."),
    ("Palm Jumeirah", "Dubai", "United Arab Emirates",
     "An island shaped like a palm tree, conjured from the sea. Lined with luxury resorts, beach "
     "clubs and sweeping ocean views, it's Dubai's most audacious feat of imagination — best seen "
     "from the air or the monorail that runs its spine."),
    ("Dubai Desert Safari", "Dubai", "United Arab Emirates",
     "Beyond the towers lie the golden dunes of the Arabian desert. Ride 4x4s over the sand, "
     "sandboard the slopes, then settle into a Bedouin camp for grilled feasts, shisha and a sky "
     "thick with stars."),
    ("Dubai Marina", "Dubai", "United Arab Emirates",
     "A glittering canyon of skyscrapers around a man-made waterfront. Stroll the promenade, cruise "
     "the harbour on a traditional dhow, and dine waterside as yachts drift past — Dubai at its "
     "most glamorous."),
    ("Old Dubai & Souks", "Dubai", "United Arab Emirates",
     "Across the creek from the glitz lies the city's soul — the spice and gold souks, abra boats "
     "crossing the water, and the restored lanes of Al Fahidi. This is where Dubai's trading "
     "history still hums."),

    # ---------------- ZANZIBAR ----------------
    ("Stone Town", "Zanzibar", "Tanzania",
     "A UNESCO-listed maze of carved doors, spice markets and coral-stone palaces, where Swahili, "
     "Arab, Indian and European worlds have met for centuries. Lose yourself in its lanes, then "
     "watch the sun sink over the harbour from a rooftop café."),
    ("Nungwi Beach", "Zanzibar", "Tanzania",
     "On Zanzibar's northern tip, Nungwi is the island at its most beautiful — powder-white sand, "
     "water in every shade of turquoise, and dhows that drift home beneath flaming sunsets. Swim, "
     "snorkel, or simply do nothing, beautifully."),
    ("Jozani Forest", "Zanzibar", "Tanzania",
     "Zanzibar's last tract of ancient forest and home to the rare red colobus monkey, found "
     "nowhere else on earth. Walk the shaded trails and mangrove boardwalks in search of these "
     "playful, russet-furred locals."),
    ("Zanzibar Spice Farms", "Zanzibar", "Tanzania",
     "Zanzibar isn't called the Spice Island for nothing. Tour a working farm to taste cloves, "
     "nutmeg, vanilla and cinnamon straight from the source, and discover the trade that shaped "
     "the island's history."),
    ("Prison Island", "Zanzibar", "Tanzania",
     "A short boat ride from Stone Town, Changuu once held a quarantine station and now shelters a "
     "colony of giant Aldabra tortoises, some over a century old. Pair it with snorkelling over "
     "the nearby reefs."),

    # ---------------- TANZANIA PARKS ----------------
    ("Mikumi", "Mikumi", "Tanzania",
     "Tanzania's accessible southern gem — open horizons where elephants, giraffes, lions and "
     "zebra roam the Mkata floodplain, reachable by road or the SGR train from Dar es Salaam."),
    ("Nyerere NP", "Nyerere", "Tanzania",
     "A vast 30,000 sq km southern wilderness (the former Selous) of woodland, lakes and the wide "
     "Rufiji River — famous for boat safaris, elephants, hippos and the rare African wild dog."),
    ("Ngorongoro", "Northern Circuit", "Tanzania",
     "The Ngorongoro Crater — a collapsed volcano cradling one of the densest concentrations of "
     "wildlife on earth, including black rhino, on its grassy floor."),
    ("Tarangire", "Northern Circuit", "Tanzania",
     "Baobab-studded plains along the Tarangire River, famous for huge elephant herds and a quieter, "
     "wilder feel than its northern neighbours."),
    ("Lake Manyara", "Northern Circuit", "Tanzania",
     "A jewel of a park beneath the Rift Valley escarpment — flamingo-pink shallows, lush groundwater "
     "forest and the famous tree-climbing lions."),

    # ---------------- EGYPT ----------------
    ("Cairo & the Pyramids", "Egypt", "Egypt",
     "Where the ancient world still stands — the Pyramids of Giza and the Sphinx on the desert's edge, "
     "and a teeming, timeless city along the Nile."),

    # ---------------- SOUTH AFRICA ----------------
    ("Cape Town", "South Africa", "South Africa",
     "Cradled between Table Mountain and two oceans, Cape Town is one of the world's most beautiful "
     "cities. Cable up the mountain, surf at Camps Bay, taste your way through the winelands and "
     "watch the sun melt into the Atlantic. Adventure, culture and scenery, all in one."),
    ("Table Mountain", "South Africa", "South Africa",
     "Cape Town's flat-topped guardian rises over a kilometre above the city. Ride the rotating "
     "cable car or hike the slopes to the summit, where the views stretch from Robben Island to "
     "the Cape of Good Hope."),
    ("Kruger National Park", "South Africa", "South Africa",
     "One of Africa's greatest game reserves, vast as a small country. Track the Big Five across "
     "golden savanna at dawn, fall asleep to the call of lions, and witness the raw drama of the "
     "African bush on a true safari."),
    ("Cape Winelands", "South Africa", "South Africa",
     "Rolling vineyards and gabled Cape Dutch estates spread across the valleys around Stellenbosch "
     "and Franschhoek. Swirl world-class wines, feast farm-to-table, and drink in some of the "
     "country's loveliest scenery."),
    ("Garden Route", "South Africa", "South Africa",
     "A spectacular ribbon of coast between Cape Town and Gqeberha, where forests, lagoons and "
     "dramatic cliffs meet the sea. Spot whales, walk ancient woodlands and follow one of the "
     "world's great scenic drives."),
    ("Robben Island", "South Africa", "South Africa",
     "A short ferry from Cape Town lies the island where Nelson Mandela was imprisoned for eighteen "
     "years. Led by former inmates, the tour is a moving journey through South Africa's road to freedom."),
]


class Command(BaseCommand):
    help = "Load destinations and landmarks with reusable travel blurbs."

    def add_arguments(self, parser):
        parser.add_argument("--with-images", action="store_true",
                            help="Also fetch 2 atmospheric photos per destination (needs internet).")

    def handle(self, *args, **options):
        created = updated = 0
        for name, region, country, blurb in DESTINATIONS:
            dest, was_created = Destination.objects.get_or_create(name=name)
            dest.region = region
            dest.country = country
            dest.description = blurb
            dest.save()
            created += was_created
            updated += (not was_created)

            if options["with_images"] and dest.images.count() < 2:
                self.stdout.write(f"  photos for {name}…", ending="")
                self.stdout.flush()
                n = self._fetch(dest, f"{name} {country}")
                self.stdout.write(self.style.SUCCESS(f" {n}") if n
                                  else self.style.WARNING(" 0"))

        self.stdout.write(self.style.SUCCESS(
            f"\n✓ {len(DESTINATIONS)} destinations ready  "
            f"({created} new, {updated} refreshed)."
        ))
        self.stdout.write("Open Admin → Destinations to see them, or add photos via the Add photos page.")

    def _fetch(self, dest, query, count=2):
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
                photographer_url=r["photographer_url"], title=r["alt"], category="destination")
            if img:
                DestinationImage.objects.create(
                    destination=dest, image=img, order=dest.destinationimage_set.count())
                added += 1
        return added

# Lara Tours — Proposal Generator

An in-house web app that turns trip details and a reusable catalog into a
branded, multi-page **PDF travel proposal**. Built to the locked spec in
[`SCOPE.md`](./SCOPE.md).

- **Catalog once**: destinations (with atmospheric photos), hotels (text),
  agents, company branding and default wording.
- **Build each proposal**: client, dates, days, pricing — then preview and export.
- **Cost + markup** pricing; the client PDF shows **final prices only**.
- **Pexels stock search** built in to fill the image library; uploads supported too.
- **8-section PDF**: cover · summary · day pages · pricing · about · closing/credits.

---

## 1. Requirements

- Python 3.10+
- The Python packages in `requirements.txt`
- **WeasyPrint system libraries** (Pango, Cairo, GDK-PixBuf). PDF export needs these:
  - **macOS**: `brew install pango gdk-pixbuf libffi`
  - **Debian/Ubuntu**: `sudo apt install libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev`
  - **Windows**: follow the WeasyPrint docs (install the GTK runtime).
  See https://doc.courtbouillon.org/weasyprint/stable/first_steps.html

The app runs without WeasyPrint — you just can't export PDFs until it's installed
(the in-browser preview still works).

## 2. Setup

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python manage.py makemigrations proposals
python manage.py migrate
python manage.py createsuperuser      # your login
python manage.py seed_demo            # demo company + 1 sample proposal
python manage.py load_destinations    # 31 destinations + landmarks, with blurbs
python manage.py load_samples         # 3 full sample proposals (add --no-images to skip photo fetch)
python manage.py load_content         # demo packages, journal posts, reviews, FAQs
python manage.py runserver
```

Open the site:
- **http://127.0.0.1:8000/** — public website (home, destinations, booking)
- **http://127.0.0.1:8000/studio/** — staff Proposal Studio (login required)
- **http://127.0.0.1:8000/admin/** — full admin, incl. **Bookings** and Company profile

Set your **Lipa Namba** under Admin → Company profile → Booking & payment so it shows
on booking confirmations. Booking flow: a client sends a request from the public site →
it appears under Admin → Bookings as *New request* → you add a quote and move it through
*Quote sent → Confirmed → Paid* as the deposit lands in your Selcom/bank.

## 3. Enable stock photo search (optional but recommended)

Get a free key at https://www.pexels.com/api/ and set it before running:

```bash
export PEXELS_API_KEY="your-key"      # Windows: set PEXELS_API_KEY=your-key
```

Then use **Image search** in the top nav to search a destination, preview results
and import the ones you like. Each import stores the photographer credit, which
auto-fills the proposal's credits page. Without a key, upload images under
*Admin → Library images*.

## 4. How you use it

1. **Set up once** (Admin):
   - *Company profile* — branding, contact, About Us, closing quote, default
     Included/Excluded/payment terms and the cover-letter template.
   - *Agents* — name, title, optional signature image.
   - *Destinations* — name + an evergreen blurb; attach photos from the library.
   - *Hotels* — name, type, room notes (text only).
2. **Per proposal** (Admin → Proposals → Add):
   - Client, travellers, dates, start/end destination, agent, cover image.
     A reference number (`YYYY-NNNN.V`) is assigned automatically.
   - Add **Days** inline (destination, narrative, accommodation, meals). Day photos
     are pulled automatically from the day's destination.
   - Add **Pricing items** inline (label, quantity, unit cost, markup %). The total
     and margins compute automatically.
3. **Preview** in the browser, then **download the PDF** (links on the proposals
   list and on each proposal in the admin).

## 5. The cover-letter template

`Company profile → letter_template` supports these placeholders:

```
{title} {client_name} {client_fullname} {travelers} {num_days} {nights}
{start_date} {end_date} {start_destination} {end_destination}
{agent_name} {company_name} {tour_length}
```

Override it for a single proposal via the proposal's *Letter & terms* section.

## 6. Project layout

```
config/            Django project (settings, urls)
proposals/
  models.py        Catalog + proposal + pricing
  admin.py         The v1 editor (inlines for days & pricing)
  images.py        Pexels search + import
  pdf.py           WeasyPrint rendering
  views.py         List, preview, PDF, image search
  templatetags/    Image-src + formatting filters
  templates/proposals/pdf/proposal.html   The 8-section brochure
  management/commands/seed_demo.py
static/css/app.css
SCOPE.md           The signed-off scope
```

## 7. Notes

- Data lives in `db.sqlite3` (back up by copying the file). Swap to PostgreSQL by
  editing `DATABASES` in `config/settings.py` — no code changes needed.
- All template wording is original to Lara Tours.
- For production: set `DJANGO_DEBUG=0`, a real `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`,
  and run `collectstatic` behind a proper web server.

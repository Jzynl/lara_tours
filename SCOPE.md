# Lara Tours — Proposal Generator
## Scope & Requirements (v1)

**Document status:** Draft for sign-off
**Owner:** Lara Tours and Travels
**Last updated:** 10 June 2026

---

## 1. Purpose

Lara Tours currently produces client proposals using SafariOffice (a third‑party SaaS).
This project builds an **in‑house web application** that produces the same kind of
**branded, multi‑page PDF proposal** from the agency's own catalog of destinations,
hotels and photos — removing the dependency on (and recurring cost of) an external tool,
and keeping all client and pricing data in‑house.

The target output is the 8‑page proposal format already in use (e.g. the
"Creating Memories with Bibi" quote for Mrs. Eileen Muyungi).

---

## 2. Goals

- Turn a small amount of trip-specific input (client, dates, days, hotels, prices)
  into a finished, professional PDF proposal in minutes.
- Build the polished descriptions and photos **once** in a reusable catalog, so every
  new proposal is mostly assembly, not writing.
- Keep all factual data (hotel names, room configs, fees, prices) **exact** — the app
  never invents or alters facts.
- Own the data: clients, proposals and pricing live in Lara Tours' own database.

### Non-goals (the problems this project is *not* trying to solve)
- It is not a booking engine, payment processor, or CRM.
- It does not auto-plan itineraries or auto-source photos from the internet.
- It is not a public, client-facing website.

---

## 3. Users & Roles

| Role | Who | What they do |
|------|-----|--------------|
| **Consultant / Agent** | Suzan Leon and colleagues | Create and edit proposals, generate PDFs |
| **Catalog manager** | Office staff | Maintain destinations, hotels, photos, standard text |
| **Admin** | Owner / IT | User accounts, branding, company profile |

v1 assumption: **one agency** (Lara Tours) with **multiple agents**. No external/multi-tenant accounts.

---

## 4. Functional Requirements (IN SCOPE)

### 4.1 Catalog (build once, reuse forever)
- **FR-1** Maintain a catalog of **Destinations** (name, region/country, evergreen description) with a set of **atmospheric photos** from the Media Library (see 4.7) — beautiful, representative shots of the place as a whole (e.g. Bali rice terraces, Dubai skyline, Zanzibar beach), not specific venues.
- **FR-2** Maintain a catalog of **Hotels / lodges** as **text** (name, type, location, room types, short blurb), optionally linked to a destination. Hotel photos are **not** required; an optional single image may be uploaded if available.
- **FR-3** Photos live in a **central, tagged Media Library** (see 4.7) and are **reused across destinations and proposals**. They are atmospheric/destination-level, each with an optional caption and an auto-captured credit.
- **FR-4** Maintain **Agents** (name, title, phone, email, optional signature image and photo).
- **FR-5** Maintain a single **Company Profile**: name, logo, tagline, contact details (phone, WhatsApp, email, website, address, country), "About Us" text, closing quote, and default Included / Excluded / Payment-terms text.

### 4.2 Proposals
- **FR-6** Create a proposal with: client title + name, number of adults and children, start date, end date, start destination, end destination, assigned agent, and a cover/hero image.
- **FR-7** Auto-generate a **reference number** in the format `YYYY-NNNN.V` (e.g. `2026-0006.2`), with a version that can be bumped for revisions.
- **FR-8** Derive trip facts automatically: tour length ("3 Days / 2 Nights"), travelers label ("2 Adults & 2 Children"), per-day dates with weekday.
- **FR-9** Generate the **cover letter** from an editable **merge template** (fields: client name, travelers, dates, start/end destinations, agent, company). Editable per proposal; no AI generation.
- **FR-10** Track proposal **status**: Draft / Sent / Confirmed.
- **FR-11** Duplicate an existing proposal as the starting point for a new one.

### 4.3 Day-by-day itinerary
- **FR-12** Add an ordered list of **Days**, each with: day number, date (auto), main destination, day type (Standard / Arrival / Departure / Leisure), and narrative text.
- **FR-13** Attach an **accommodation** entry per day: hotel (from catalog), room configuration text ("1x Single Room & 1x Single Room"), and a short stay blurb.
- **FR-14** Set a **meal plan** per day as any combination of Breakfast / Lunch / Dinner, rendered as "Breakfast, Lunch & Dinner".
- **FR-15** Day pages pull **atmospheric photos automatically** from the day's destination in the Media Library. Special day types (Departure/Leisure) render a reduced layout.
- **FR-16** Pre-fill narrative and blurbs from editable defaults, overridable per day.

### 4.4 Pricing (cost + markup)
- **FR-17** Add **pricing line items** (e.g. "Adult", "Child", "Transfer") with quantity, **unit cost**, and a **markup %**.
- **FR-18** Compute unit price = cost × (1 + markup), line total = unit price × quantity, and a grand **Total** in the proposal currency.
- **FR-19** Show **cost, markup and margin internally**, but the client PDF shows **only the final prices and total** (cost/markup never leak to the client page).
- **FR-20** Editable **payment terms** and **Included / Excluded** lists per proposal (defaulted from the company profile).

### 4.5 PDF output (the deliverable)
- **FR-21** Generate the full **8-section PDF**:
  1. **Cover** — hero image, ref number, client name, four fact boxes, title + eyebrow, merge-letter, agent name/signature/contact.
  2. **Summary** — thumbnail, dates, Day-by-Day table (Day · Destination · Accommodation · Meal Plan) with timeline, start/end destinations.
  3–N. **One page per day** — header bar, title, narrative, accommodation block (text), meal-plan box, atmospheric destination photo gallery.
  - **Pricing** — fact boxes, cost breakdown, total, payment terms, Included / Excluded.
  - **About Us / Contact** — company story and details.
  - **Closing** — quote + colophon that **auto-lists photo credits** for every stock image used (photographer + source).
- **FR-22** Every page carries the **branded footer**: page number, ref number, client name, company name.
- **FR-23** Provide an in-browser **preview** of the proposal before download.
- **FR-24** PDF filename is derived from the ref number and client (e.g. `Proposal_2026-0006-2_Eileen-Muyungi.pdf`).

### 4.6 Application / management
- **FR-25** List all proposals with search/filter by client, ref, status, date.
- **FR-26** All catalog and proposal editing available through a secure admin interface (Django admin in v1).
- **FR-27** Login-protected; only authenticated staff can view or generate proposals.

### 4.7 Media Library & stock photo search
- **FR-28** Maintain a **central Media Library** of images, each with: image file, auto-generated thumbnail, title/caption, **tags** (place + vibe, e.g. "bali", "beach", "luxury"), category (Destination / Hero / Mood / Food / Culture), and optional **credit (photographer + source URL) and license** fields.
- **FR-29** **Stock search is the primary fill method**; **manual upload** is also supported for any photos the agency already has on hand.
- **FR-30** **Search licensed stock (Pexels)** from inside the app: enter a query, browse results, pick an image, and **import** it into the library with the photographer credit and source captured automatically.
- **FR-31** **Search and filter** the library by tag, category or text; reuse any image across multiple catalog items and proposals.
- **FR-32** Images are **reused by reference**, not copied — updating an image once updates it everywhere it is used in future renders.
- **FR-33** The proposal's **credits/colophon page** is generated automatically, listing the photographer/source for every stock image used.
- **FR-34** Stock search degrades gracefully: if no API key is configured or the service is unreachable, uploads still work and search is simply disabled with a clear message.

---

## 5. Out of Scope (v1 — explicitly NOT included)

- ❌ **Online payments / deposits** — the PDF states payment terms only.
- ❌ **Client portal / online acceptance** — "Confirm Booking" is text, not a live button.
- ❌ **Auto-inserting images** / web scraping — images are chosen by a person (via stock search or upload), never auto-inserted from arbitrary web results.
- ❌ **AI-written descriptions** — text is catalog boilerplate + merge templates.
- ❌ **Automatic day/route planning** — the agent assigns days manually.
- ❌ **Multi-agency / multi-tenant SaaS** — single agency only.
- ❌ **Live availability or hotel/airline API integration.**
- ❌ **Currency conversion / multi-currency math** — one currency per proposal.
- ❌ **Email sending from the app** — agent downloads the PDF and sends it themselves.
- ❌ **Mobile native apps** — responsive web admin only.
- ❌ **Drag-and-drop visual builder** — ordering via the admin in v1 (candidate for v2).

---

## 6. Non-Functional Requirements

### 6.1 Performance
- **NFR-1** A typical proposal (6–8 pages, ~20 images) generates a PDF in **under ~10 seconds** on a modest server.
- **NFR-2** Admin list and edit pages load in **under 2 seconds** with up to a few thousand proposals.

### 6.2 Usability
- **NFR-3** A trained consultant can produce a complete proposal from catalog items in **under 15 minutes**.
- **NFR-4** Output is **print-ready A4** with consistent margins, fonts and brand colours on every page.
- **NFR-5** Admin works on a standard desktop browser (Chrome/Edge/Firefox/Safari, current versions).

### 6.3 Reliability & data integrity
- **NFR-6** Factual fields (names, room configs, fees, prices) are stored and rendered **verbatim**; no transformation.
- **NFR-7** Reference numbers are **unique** and never reused.
- **NFR-8** Daily database file backup is supported (SQLite file copy; documented procedure).

### 6.4 Security
- **NFR-9** All pages require authentication; no anonymous access to client data.
- **NFR-10** CSRF protection, hashed passwords, and secret key from environment (Django defaults).
- **NFR-11** Uploaded media stored on the server filesystem, not publicly listable.

### 6.5 Maintainability & portability
- **NFR-12** Built on **Django (Python)** with a clear catalog/proposal/pricing/pdf separation.
- **NFR-13** Runs on **SQLite** out of the box (single-office use); upgradeable to PostgreSQL without code rewrite.
- **NFR-14** Runs on Windows, macOS or Linux with Python 3.10+; documented setup in the README.
- **NFR-15** Branding, default texts and the letter template are **data, not code** — editable without a developer.

### 6.6 Capacity
- **NFR-16** Handles the realistic volume of a single agency: thousands of proposals, hundreds of catalog items, with images.

### 6.7 Localization
- **NFR-17** English UI and output; dates in long form ("Friday, May 1, 2026"); currency symbol per proposal. Timezone Africa/Dar_es_Salaam.

---

## 7. Data Entities (summary)

`CompanyProfile` · `Agent` · `MediaImage` (+ `Tag`) · `Destination` (references images by tag) ·
`Hotel` (text, optional single image) · `Proposal` (the trip) · `Day` (pulls destination images) · `PricingItem`.

---

## 8. Assumptions & Constraints

- One agency (Lara Tours), multiple agents.
- One currency per proposal; prices entered as cost + markup %.
- Photos are **atmospheric, destination-level** — gorgeous representative shots, not specific hotels or venues.
- Stock images come from **Pexels** (free for commercial use); a free Pexels API key is required for in-app search. Uploads work without it.
- PDF rendering uses **WeasyPrint**, which requires its system libraries (documented in README).
- Template wording is **original to Lara Tours** — the third-party tool's copy is not reused.

---

## 9. Definition of Done (acceptance)

The v1 is accepted when:
1. Staff can log in and manage destinations, the image library, agents and company profile.
2. A consultant can create a proposal, add days and pricing, and preview it in the browser.
3. Generating the PDF produces all 8 sections, branded, with correct facts, photos, captions, meal plans, totals and footers.
4. The client PDF shows final prices only — never cost or markup.
5. A reference number is assigned automatically and is unique.

---

## 10. Likely v2 / later

- Drag-and-drop day & item ordering.
- Email the PDF (or a secure link) directly to the client.
- Online proposal acceptance / e-signature.
- Optional photo search to *suggest* (not auto-insert) catalog images.
- Multi-currency and per-item taxes.
- Reusable full-trip "packages" (e.g. a standard 6-day Bali template) to start a proposal from.

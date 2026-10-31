#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate 10 new English buying-guide pages under en/guides/ for jinbacars.com.

Reuses the existing guide page shell (header/footer/styles/GA4) so the new
pages match the live design system. Also appends link cards to en/guides/index.html.
Run: python scripts/gen_guides_20261030.py
"""
from __future__ import annotations

import html
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
GUIDES = ROOT / "en" / "guides"
BASE = GUIDES / "vehicle-inspection-checklist" / "index.html"

OLD_TITLE = "Used vehicle inspection checklist"
OLD_SLUG = "vehicle-inspection-checklist"
OLD_DESC = (
    "Used vehicle inspection checklist. Use this checklist to discuss sourcing a used vehicle from China. "
    "Each vehicle, route and destination must be checked separat"
)

WA = "https://wa.me/8618079089999"

ARTICLES = [
    {
        "slug": "cheapest-used-cars-from-china-under-10000",
        "title": "Cheapest Used Cars from China Under $10,000",
        "desc": "Which used cars from China cost under $10,000 for export, what the price actually includes, and how to compare FOB and CIF quotes before you order.",
        "sections": [
            ("What $10,000 actually buys", "<p>Under $10,000 the export market is dominated by compact sedans, small SUVs and the first generation of Chinese electric cars. Most units in that band are 2019-2022 model years with 30,000-90,000 km. Condition varies far more at this price than at $20,000, so ask for a dated photo set and an inspection report on the exact unit, not on the model in general.</p>"),
            ("Models that commonly trade in this band", "<ul><li><strong>Geely Emgrand</strong> - sedan on a Volvo-derived platform, simple mechanicals, widely available parts.</li><li><strong>Changan CS55</strong> - compact SUV, usually the cheapest credible high-clearance option.</li><li><strong>Haval H6 (older years)</strong> - larger SUV body, but early-year examples sit at the top of this budget.</li><li><strong>BYD e5 / Qin EV</strong> - electric sedans, cheap to run, but battery health must be documented.</li></ul>"),
            ("What the price includes - and what it does not", "<p>A quoted number is only comparable when the trade term is stated. FOB covers the vehicle and loading at the Chinese port. CIF adds ocean freight and marine insurance to your destination port. Neither covers import duty, clearing agents, port storage or inland transport at your end. Two suppliers quoting '$8,500' can differ by several thousand dollars once the term and destination are clear.</p>"),
            ("Questions to ask before paying a deposit", "<ul><li>Is the quote FOB or CIF, and to which port?</li><li>Does the unit have a documented battery state of health (for EVs)?</li><li>Which model year and which drive configuration - left-hand drive is required in most African markets?</li><li>What is the exact VIN, and can you receive photos of that VIN?</li></ul><p>Answer these in writing before any payment. A supplier who cannot answer them is not ready to export.</p>"),
        ],
        "related": [
            ("/en/cars/", "Used cars from China"),
            ("/en/guides/roro-vs-container-shipping-cars-from-china/", "RORO vs container shipping"),
            ("/en/guides/car-import-duty-and-tax-calculation-africa/", "Import duty calculation"),
        ],
    },
    {
        "slug": "used-cars-from-china-to-ghana",
        "title": "Importing Used Cars from China to Ghana",
        "desc": "How used car import to Ghana works from China: age limits, Tema and Takoradi routes, document set, and what to confirm before you commit to a unit.",
        "sections": [
            ("Age and condition rules", "<p>Ghana applies an age-based penalty scale to used vehicle imports, which means an older unit can attract a materially higher duty rate than a newer one of the same value. Confirm the current scale for your model year with a licensed clearing agent before you choose a vehicle, because the scale is revised periodically and it changes the total landed cost more than the vehicle price does.</p>"),
            ("Ports and routing", "<p>Most vehicle imports arrive at Tema, with Takoradi used for the western corridor. RORO is the usual choice for a single unit; container shipping is used when you consolidate several vehicles or when the unit is not driveable. Ask the supplier which service they actually booked, because RORO and container have different terminal handling charges at destination.</p>"),
            ("Documents you should receive", "<ul><li>Commercial invoice matching the declared value</li><li>Bill of Lading with the consignee details you specified</li><li>Certificate of Origin</li><li>Export declaration from China</li><li>Payment receipt</li></ul><p>Check that the consignee name on the Bill of Lading is exactly the entity that will clear the vehicle. Correcting it after the vessel sails is slow and expensive.</p>"),
            ("Left-hand drive and specification", "<p>Ghana drives on the right, so left-hand drive is required. Confirm LHD in writing. Also confirm whether the unit has a catalytic converter and the emission standard it meets, because both can affect clearance.</p>"),
            ("Budget beyond the vehicle price", "<p>Plan for duty and levies, clearing agent fees, terminal charges, port storage if clearance is slow, and inland transport to your city. Importers who budget only the CIF number are the ones who end up with a vehicle sitting at the port accruing storage charges.</p>"),
        ],
        "related": [
            ("/en/guides/import-china-cars-to-nigeria/", "Import to Nigeria"),
            ("/en/guides/import-china-cars-to-kenya/", "Import to Kenya"),
            ("/en/guides/export-documents-and-shipping/", "Export documents"),
        ],
    },
    {
        "slug": "roro-vs-container-shipping-cars-from-china",
        "title": "RORO vs Container: Shipping Cars from China",
        "desc": "RORO and container shipping compared for used car export from China: cost drivers, damage risk, consolidation, and how to pick the right service.",
        "sections": [
            ("How RORO works", "<p>Roll-on/roll-off vessels load the vehicle by driving it aboard. You pay for the slot, not for a container. RORO is usually the cheapest option for a single driveable car and it is the standard service on high-volume routes such as China to West Africa and China to the Gulf. The trade-off is that you cannot add parts or personal effects inside the vehicle, and the sailing schedule follows the vessel's port rotation rather than your convenience.</p>"),
            ("How container shipping works", "<p>The vehicle is lashed inside a 20ft or 40ft container. This is the better choice when you ship several vehicles, when the unit is not driveable, or when you need to include spare parts. A 40ft high-cube container can often take two smaller vehicles with careful loading, which changes the per-unit economics completely.</p>"),
            ("Cost comparison that actually holds", "<p>There is no universal winner. RORO wins on single-unit simplicity. Container wins as soon as you share the box. Compare total cost per vehicle at destination, including terminal handling, not just the ocean freight line.</p><ul><li>One driveable car, one buyer: RORO is normally cheaper.</li><li>Two or three cars for one consignee: a shared container usually beats multiple RORO slots.</li><li>Non-running or damaged unit: container or flat rack, not RORO.</li><li>Shipping spare parts with the car: container.</li></ul>"),
            ("Damage and insurance", "<p>Both services carry risk. RORO risk is concentrated at loading and discharge; container risk is concentrated in lashing quality and in condensation on long voyages. In both cases, photograph the vehicle at loading, keep the survey report, and make sure marine insurance covers the full CIF value. A claim without loading photos is very hard to win.</p>"),
            ("What to confirm in the quotation", "<ul><li>Service type and vessel or container reference</li><li>Port of loading and port of discharge</li><li>Whether freight is prepaid or collect</li><li>Free time at destination before storage charges begin</li></ul>"),
        ],
        "related": [
            ("/en/guides/shipping-time-from-china-to-africa/", "Shipping transit times"),
            ("/en/guides/export-documents-and-shipping/", "Export documents"),
            ("/en/guides/car-import-duty-and-tax-calculation-africa/", "Import duty calculation"),
        ],
    },
    {
        "slug": "best-chinese-suvs-for-africa",
        "title": "Best Chinese SUVs for African Roads",
        "desc": "Which Chinese SUVs work best for African markets: ground clearance, parts availability, fuel tolerance and resale, with models to compare.",
        "sections": [
            ("What actually matters on African roads", "<p>Three things decide whether an SUV survives well: ground clearance, suspension durability and parts availability. A premium badge with 160mm of clearance and no local parts network is a worse commercial choice than a modest Chinese SUV with 190mm of clearance and a dealer two hours away. Buyers who ignore this end up importing vehicles that are expensive to keep on the road.</p>"),
            ("Models worth comparing", "<ul><li><strong>Haval H6</strong> - the most established Chinese SUV in African markets, with the widest parts and service coverage. Ride comfort is good; early dual-clutch examples need a careful test drive.</li><li><strong>Changan CS75 / CS55</strong> - typically cheaper than Haval for similar size, with simpler mechanicals on the CS55.</li><li><strong>Geely Boyue / Atlas</strong> - Volvo-derived platform, strong safety structure, good highway behaviour.</li><li><strong>GAC GS4 / GS8</strong> - joint-venture build quality, growing parts presence.</li><li><strong>BYD Song Plus</strong> - plug-in hybrid or EV, low running cost, but only where charging or hybrid service exists.</li></ul>"),
            ("Petrol, hybrid or electric", "<p>Petrol remains the safest choice where fuel quality varies and workshop familiarity is limited. Hybrids make sense for high-mileage urban fleets. Full EVs make sense only where charging is reliable and where the buyer understands battery degradation. Do not import an EV into a market with no service capability and expect the resale value to hold.</p>"),
            ("Specification checks before ordering", "<ul><li>Left-hand drive, confirmed in writing</li><li>Ground clearance and tyre size for the roads it will actually use</li><li>Whether the engine tolerates the local fuel octane and sulphur level</li><li>Availability of filters, brake pads and suspension bushes in the destination market</li></ul>"),
        ],
        "related": [
            ("/en/chinese-cars/", "Chinese cars for export"),
            ("/en/guides/left-hand-drive-cars-export-from-china/", "Left-hand drive export"),
            ("/en/guides/chinese-car-brands-parts-availability-africa/", "Parts availability"),
        ],
    },
    {
        "slug": "car-import-duty-and-tax-calculation-africa",
        "title": "How Import Duty Is Calculated on a Used Car",
        "desc": "How African governments calculate duty on imported used cars, what CIF means for the taxable base, and how to budget the landed cost before ordering.",
        "sections": [
            ("The taxable base is not the price you paid", "<p>Most customs authorities assess duty on a value they determine themselves, usually derived from CIF plus a reference value for the model and year. Paying $9,000 for a car does not guarantee that duty is calculated on $9,000. This is the single most common budgeting error importers make, and it is why a clearing agent's estimate before purchase is worth more than any online calculator.</p>"),
            ("The usual components", "<ul><li>Import duty, often banded by engine size, model year or vehicle type</li><li>Value added tax or equivalent consumption tax</li><li>Levies, inspection fees and port charges</li><li>Age-based penalties in markets with vehicle age limits</li></ul><p>Rates differ by country and are revised. Treat any percentage you see online, including on this page, as a prompt to verify rather than a quote.</p>"),
            ("Worked example of the method", "<p>Assume a CIF value of $10,000. If the applicable duty is 20% and VAT is 15% charged on the duty-inclusive value, the arithmetic is: duty $2,000, subtotal $12,000, VAT $1,800, total tax $3,800. Add clearing, terminal and transport costs and you have the landed cost. Change any single rate and the total moves by hundreds of dollars, which is why the rate check has to happen before purchase.</p>"),
            ("Getting a usable estimate", "<p>Give a licensed agent in the destination country the VIN, model year, engine size and CIF value, and ask for a written estimate that separates duty, VAT and fees. Compare that estimate against the vehicle price. If the landed cost is above what the vehicle sells for locally, the deal does not work regardless of how good the unit is.</p>"),
            ("Costs people forget", "<ul><li>Port storage after the free period</li><li>Clearing agent commission</li><li>Inland transport from port to city</li><li>Registration and plates at destination</li></ul>"),
        ],
        "related": [
            ("/en/guides/import-china-cars-to-nigeria/", "Import to Nigeria"),
            ("/en/guides/used-cars-from-china-to-ghana/", "Import to Ghana"),
            ("/en/guides/safe-payment-and-quotation/", "Safe quotation checks"),
        ],
    },
    {
        "slug": "shipping-time-from-china-to-africa",
        "title": "Shipping Time from China to Africa",
        "desc": "Realistic transit times for used cars shipped from China to African ports, stage by stage, and why the vessel schedule is only part of the timeline.",
        "sections": [
            ("The timeline has five stages", "<p>Buyers usually quote the ocean leg and forget the rest. A realistic plan covers: vehicle release and inspection, export customs, ocean transit, destination clearance, and inland delivery. Only the middle stage is fixed by the shipping line.</p><ul><li><strong>Release and inspection</strong> - 2 to 7 days, longer if a repair or part is needed</li><li><strong>Export customs and loading</strong> - 3 to 7 days</li><li><strong>Ocean transit</strong> - 25 to 40 days to West Africa, 20 to 30 days to East Africa, depending on rotation</li><li><strong>Destination clearance</strong> - 5 to 20 days, driven by documentation quality and duty payment speed</li><li><strong>Inland delivery</strong> - 1 to 10 days</li></ul>"),
            ("Why the ocean leg varies so much", "<p>RORO vessels follow a rotation, so a port that is served weekly is very different from one served monthly. Transhipment adds days and adds handling risk. If timing matters, ask for the specific vessel and the estimated arrival at your port, and accept that the estimate moves.</p>"),
            ("Where delays actually come from", "<p>In our experience the delays that hurt are not at sea. They come from a consignee name that does not match on the Bill of Lading, a duty payment that waits for a bank transfer, or an inspection that finds an undeclared item. Every one of those is preventable before the vessel sails.</p>"),
            ("Planning backwards from a date", "<p>If you need the vehicle on the ground by a certain date, work backwards: inland delivery, clearance, ocean transit, loading, release. Add two weeks of buffer. A supplier who promises a fixed arrival date without buffer is guessing.</p>"),
        ],
        "related": [
            ("/en/guides/roro-vs-container-shipping-cars-from-china/", "RORO vs container"),
            ("/en/guides/import-china-cars-to-kenya/", "Import to Kenya"),
            ("/en/guides/used-cars-from-china-to-tanzania/", "Import to Tanzania"),
        ],
    },
    {
        "slug": "left-hand-drive-cars-export-from-china",
        "title": "Left-Hand Drive Cars for Export from China",
        "desc": "Why left-hand drive matters for African and Middle East imports, how to confirm LHD in writing, and what to check on the vehicle documents.",
        "sections": [
            ("Which markets need LHD", "<p>Most of Africa, the Middle East and Central Asia drive on the right and therefore require left-hand drive vehicles. Notable right-hand drive markets in Africa include Kenya, Tanzania, Uganda and South Africa. Ordering the wrong configuration is not a paperwork problem, it is a vehicle that cannot be legally registered, so it belongs in the first message, not the last.</p>"),
            ("Why the Chinese domestic market is mostly LHD", "<p>China drives on the right, so the domestic fleet is overwhelmingly left-hand drive. That is an advantage for exporters shipping to Africa and the Gulf: the vehicles do not need conversion, and the specification is native rather than adapted. Right-hand drive export units exist but are a smaller pool and command different pricing.</p>"),
            ("How to confirm LHD", "<p>Do not accept 'yes, LHD' as an answer. Ask for a photograph of the interior showing the steering wheel position, and check that the VIN on the photo of the door jamb matches the VIN on the invoice. For markets that inspect on arrival, keep that evidence with the shipping documents.</p>"),
            ("Other specification points tied to the destination", "<ul><li>Speedometer units - km/h versus mph</li><li>Air conditioning rated for the local climate</li><li>Emission standard and catalytic converter present</li><li>Fuel octane tolerance where fuel quality varies</li><li>Spare wheel or tyre repair kit supplied</li></ul>"),
        ],
        "related": [
            ("/en/cars/", "Used cars from China"),
            ("/en/guides/best-chinese-suvs-for-africa/", "Best Chinese SUVs"),
            ("/en/guides/vehicle-inspection-checklist/", "Inspection checklist"),
        ],
    },
    {
        "slug": "used-electric-cars-from-china-running-cost",
        "title": "Used Electric Cars from China: Running Cost Reality",
        "desc": "What a used EV from China actually costs to run versus petrol, how to read battery health data, and when an EV import makes commercial sense.",
        "sections": [
            ("The arithmetic that matters", "<p>An EV's advantage is entirely in the running cost, so the comparison only works if you use real local prices. Take annual distance, local electricity price per kWh, local petrol price, and the vehicle's consumption. Then add maintenance, which is lower on an EV mainly because there is no oil, fewer filters and regenerative braking that extends pad life.</p>"),
            ("Illustrative comparison", "<p>At 30,000 km per year, a compact electric sedan consuming around 15 kWh per 100 km uses roughly 4,500 kWh annually. At $0.10 per kWh that is about $450. A petrol equivalent at 7 L per 100 km uses about 2,100 litres; at $1.20 per litre that is about $2,520. The gap is real, but only if the electricity price and charging access are real.</p>"),
            ("Battery health is the whole valuation", "<p>A used EV without a battery state-of-health report is a speculative purchase. Ask for a state-of-health percentage from a diagnostic session, the cell balance summary, and the number of fast-charge cycles where available. A pack at 85% of original capacity behaves very differently from one at 70%, and replacement cost can exceed the vehicle's value.</p>"),
            ("When an EV import makes sense", "<ul><li>Urban or peri-urban fleet with predictable daily distance</li><li>Reliable charging at a depot, not dependence on public charging</li><li>Local technician capability for high-voltage systems</li><li>Buyer who understands degradation and resale risk</li></ul><p>Outside those conditions, a petrol or hybrid unit is the more defensible commercial decision.</p>"),
        ],
        "related": [
            ("/en/guides/used-ev-export-china-byd/", "Used EV export and BYD"),
            ("/en/guides/cheapest-used-cars-from-china-under-10000/", "Cars under $10,000"),
            ("/en/guides/vehicle-inspection-checklist/", "Inspection checklist"),
        ],
    },
    {
        "slug": "used-cars-from-china-to-tanzania",
        "title": "Importing Used Cars from China to Tanzania",
        "desc": "Used car import to Tanzania from China: right-hand drive requirement, Dar es Salaam routing, pre-shipment inspection and the documents you need.",
        "sections": [
            ("Right-hand drive is mandatory", "<p>Tanzania drives on the left, so right-hand drive is required. This is the single largest constraint on sourcing from China, because the Chinese domestic fleet is almost entirely left-hand drive. Confirm RHD availability before discussing price, and expect a smaller and differently priced pool than for West African destinations.</p>"),
            ("Pre-shipment inspection", "<p>Tanzania requires a pre-shipment inspection for used vehicle imports, carried out by an approved inspection company in the country of export. The certificate is part of the clearance file. If the unit fails inspection at origin, it does not ship, which is better than finding out at Dar es Salaam. Ask the supplier which inspection body will handle it and when.</p>"),
            ("Routing and destination costs", "<p>Dar es Salaam is the main port. Landlocked neighbours such as Zambia, Malawi and the DRC also clear through Dar es Salaam, which makes the port busy and makes documentation accuracy more valuable, not less. Budget for terminal charges, agent fees and inland transport separately from freight.</p>"),
            ("Documents to assemble", "<ul><li>Commercial invoice</li><li>Bill of Lading</li><li>Certificate of Origin</li><li>Pre-shipment inspection certificate</li><li>Export declaration from China</li></ul><p>Keep a scanned copy of every document in one folder before the vessel sails.</p>"),
            ("Age and condition expectations", "<p>Tanzania applies age-related restrictions and penalties on used imports, so confirm the current rule for your model year with a local clearing agent before committing. A unit that is one year too old can change the landed cost enough to break the deal.</p>"),
        ],
        "related": [
            ("/en/guides/import-china-cars-to-kenya/", "Import to Kenya"),
            ("/en/guides/shipping-time-from-china-to-africa/", "Shipping transit times"),
            ("/en/guides/export-documents-and-shipping/", "Export documents"),
        ],
    },
    {
        "slug": "chinese-car-brands-parts-availability-africa",
        "title": "Chinese Car Brands: Parts Availability in Africa",
        "desc": "Which Chinese car brands have the best parts and service coverage in African markets, and how to check availability before you import a model.",
        "sections": [
            ("Why parts availability decides resale value", "<p>A vehicle that needs a three-month wait for a suspension bush is worth less than the same vehicle with a local parts network, no matter how good the specification is. Fleet buyers know this and price accordingly. If you import for resale, parts coverage is not a detail, it is the product.</p>"),
            ("Brand positioning in practice", "<ul><li><strong>Haval / GWM</strong> - the broadest dealer and parts presence among Chinese brands in Africa, particularly in West and East Africa.</li><li><strong>BYD</strong> - expanding quickly, strongest where electric and hybrid fleets are being adopted.</li><li><strong>Changan</strong> - growing presence, common wear parts are increasingly available.</li><li><strong>Geely</strong> - strong product quality, coverage varies sharply by country.</li><li><strong>GAC</strong> - joint-venture build quality, coverage concentrated in larger markets.</li></ul><p>Coverage changes. Verify locally rather than relying on a general ranking.</p>"),
            ("How to check before you buy", "<p>Call two independent workshops in the destination city and ask whether they can source a brake pad set and a front lower arm for the specific model and year. If both say yes within a week, the model is supportable. If both hesitate, the resale risk is yours.</p>"),
            ("Buying a parts kit with the vehicle", "<p>For fleet purchases, shipping a consumables kit with the cars is often the cheapest insurance available: filters, brake pads, belts, wiper blades and one set of common suspension bushes. In a shared container the marginal freight cost is small compared with the downtime it prevents.</p>"),
        ],
        "related": [
            ("/en/chinese-cars/", "Chinese cars for export"),
            ("/en/guides/best-chinese-suvs-for-africa/", "Best Chinese SUVs"),
            ("/en/wholesale-used-cars/", "Wholesale used cars from China"),
        ],
    },
]


def build_page(base: str, art: dict) -> str:
    page = base
    page = page.replace(OLD_TITLE, art["title"])
    page = page.replace(OLD_SLUG, art["slug"])
    page = page.replace(OLD_DESC, art["desc"])
    page = page.replace('"dateModified": "2026-10-09"', '"dateModified": "2026-10-30"')
    # 新页面只有英文版，移除指向不存在语言版本的 hreflang，避免搜索引擎抓取 404
    for lang in ("zh", "ru", "ar"):
        page = re.sub(
            r'<link rel="alternate" hreflang="%s" href="[^"]*">' % lang, "", page
        )

    body_parts = []
    for h2, inner in art["sections"]:
        body_parts.append("<section><h2>%s</h2>%s</section>" % (h2, inner))
    related_li = "".join(
        '<li><a href="%s">%s</a></li>' % (href, label) for href, label in art["related"]
    )
    aside = '<aside class="checkpanel"><h2>Related buying resources</h2><ul>%s</ul></aside>' % related_li

    new_inner = "".join(body_parts) + aside
    page = re.sub(
        r'(<div class="articlebody">).*?(<div class="actions">)',
        lambda m: m.group(1) + new_inner + m.group(2),
        page,
        flags=re.S,
    )
    return page


def main() -> None:
    base = BASE.read_text(encoding="utf-8")
    made = []
    for art in ARTICLES:
        out_dir = GUIDES / art["slug"]
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "index.html").write_text(build_page(base, art), encoding="utf-8")
        made.append(art)

    # 追加到 guides 列表页
    idx_path = GUIDES / "index.html"
    idx = idx_path.read_text(encoding="utf-8")
    cards = []
    for art in made:
        if ('href="/en/guides/%s/"' % art["slug"]) in idx:
            continue
        cards.append(
            '<a class="linkcard" href="/en/guides/%s/"><h2>%s</h2><p>%s</p><span>\u2192</span></a>'
            % (art["slug"], html.escape(art["title"]), html.escape(art["desc"]))
        )
    new_cards = "".join(cards)
    if new_cards:
        idx = idx.replace("</div></div></main>", new_cards + "</div></div></main>", 1)
        idx_path.write_text(idx, encoding="utf-8")

    print("generated:", len(made))
    for art in made:
        print("  en/guides/%s/" % art["slug"])


if __name__ == "__main__":
    main()

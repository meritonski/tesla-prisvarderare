import asyncio
import csv
import re
from datetime import datetime
from urllib.parse import urlencode, urljoin, urlparse

from playwright.async_api import async_playwright


BASE_URL = "https://www.blocket.se/annonser/hela_sverige/fordon/bilar"

SEARCHES = [
    {
        "make": "Tesla",
        "model": "Model Y",
        "variant": "Performance",
        "display_name": "Tesla Model Y Performance",
        "query": "Tesla Model Y Performance",
        "required_terms": ["tesla", "model y"],
    },
    {
        "make": "Tesla",
        "model": "Model Y",
        "variant": "Long Range",
        "display_name": "Tesla Model Y Long Range",
        "query": "Tesla Model Y Long Range",
        "required_terms": ["tesla", "model y"],
    },
    {
        "make": "Audi",
        "model": "RS e-tron GT",
        "variant": "RS",
        "display_name": "Audi RS e-tron GT",
        "query": "Audi RS e-tron GT",
        "required_terms": ["audi", "e-tron", "gt"],
    },
    {
        "make": "Audi",
        "model": "e-tron GT",
        "variant": "GT",
        "display_name": "Audi e-tron GT",
        "query": "Audi e-tron GT",
        "required_terms": ["audi", "e-tron", "gt"],
    },
    {
        "make": "Porsche",
        "model": "Taycan",
        "variant": "Taycan",
        "display_name": "Porsche Taycan",
        "query": "Porsche Taycan",
        "required_terms": ["porsche", "taycan"],
    },
    {
        "make": "BMW",
        "model": "i4",
        "variant": "i4",
        "display_name": "BMW i4",
        "query": "BMW i4",
        "required_terms": ["bmw", "i4"],
    },
    {
        "make": "Polestar",
        "model": "2",
        "variant": "Polestar 2",
        "display_name": "Polestar 2",
        "query": "Polestar 2",
        "required_terms": ["polestar"],
    },
    {
        "make": "Kia",
        "model": "EV6",
        "variant": "EV6",
        "display_name": "Kia EV6",
        "query": "Kia EV6",
        "required_terms": ["kia", "ev6"],
    },
]

OUTPUT_FILE = "ev_market_database.csv"
DEBUG_LINKS_FILE = "candidate_links_debug.csv"

MAX_SEARCH_PAGES = 20
MAX_DETAIL_PAGES_PER_SEARCH = 250

SEARCH_PAGE_DELAY_MS = 4000
DETAIL_PAGE_DELAY_MS = 1500
BETWEEN_DETAILS_DELAY_MS = 1000


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def parse_price(text: str):
    if not text:
        return None

    matches = re.findall(r"([\d\s]{3,})\s*kr", text.lower())
    prices = []

    for match in matches:
        try:
            value = int(match.replace(" ", ""))
            if 50000 <= value <= 2500000:
                prices.append(value)
        except Exception:
            pass

    if not prices:
        return None

    return prices[0]


def parse_mileage_km(text: str):
    if not text:
        return None

    lower = text.lower()

    mil_matches = re.findall(r"([\d\s]{1,8})\s*mil\b", lower)
    for match in mil_matches:
        try:
            value = int(match.replace(" ", ""))
            if 0 <= value <= 50000:
                return value * 10
        except Exception:
            pass

    km_matches = re.findall(r"([\d\s]{1,8})\s*km\b", lower)
    for match in km_matches:
        try:
            value = int(match.replace(" ", ""))
            if 0 <= value <= 500000:
                return value
        except Exception:
            pass

    return None


def parse_year(text: str):
    if not text:
        return None

    matches = re.findall(r"\b(20[0-2][0-9])\b", text)

    for match in matches:
        year = int(match)
        if 2010 <= year <= 2027:
            return year

    return None


def normalize_url(href: str) -> str:
    if not href:
        return ""

    href = href.strip()
    href = urljoin("https://www.blocket.se", href)
    href = href.split("#")[0]

    return href


def is_blocket_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return "blocket.se" in parsed.netloc
    except Exception:
        return False


def is_real_ad_url(url: str) -> bool:
    if not url:
        return False

    if not is_blocket_url(url):
        return False

    parsed = urlparse(url)
    path = parsed.path.lower()

    return path.startswith("/mobility/item/")


def normalize_for_match(text: str) -> str:
    lower = text.lower()
    lower = lower.replace("-", " ")
    lower = lower.replace("_", " ")
    lower = lower.replace("é", "e")
    lower = re.sub(r"\s+", " ", lower)
    return lower


def text_contains_term(text: str, term: str) -> bool:
    normalized_text = normalize_for_match(text)
    normalized_term = normalize_for_match(term)

    if normalized_term in normalized_text:
        return True

    # Specialfall för e-tron/etron
    if normalized_term == "e tron":
        return "e tron" in normalized_text or "etron" in normalized_text

    return False


def detail_text_is_relevant(text: str, url: str, search: dict) -> bool:
    if not is_real_ad_url(url):
        return False

    combined = f"{text} {url}"

    for term in search["required_terms"]:
        if not text_contains_term(combined, term):
            return False

    # Stoppa tydliga felträffar för Tesla.
    normalized = normalize_for_match(combined[:500])
    if search["make"] == "Tesla" and search["model"] == "Model Y":
        bad_models = ["model 3", "model s", "model x"]
        for bad in bad_models:
            if bad in normalized:
                return False

    return True


def text_looks_like_car_card(text: str) -> bool:
    lower = normalize_for_match(text)

    indicators = [
        "kr",
        "mil",
        "km",
        "automat",
        "el",
        "awd",
        "tesla",
        "audi",
        "porsche",
        "bmw",
        "polestar",
        "kia",
        "taycan",
        "e tron",
        "etron",
        "model y",
        "ev6",
        "i4",
    ]

    score = 0

    for indicator in indicators:
        if indicator in lower:
            score += 1

    return score >= 2


async def accept_cookies(page):
    cookie_buttons = [
        "button:has-text('Acceptera')",
        "button:has-text('Godkänn')",
        "button:has-text('Tillåt alla')",
        "button:has-text('Acceptera alla')",
        "button:has-text('Accept')",
        "button:has-text('Accept all')",
    ]

    for selector in cookie_buttons:
        try:
            count = await page.locator(selector).count()
            if count > 0:
                await page.locator(selector).first.click(timeout=2000)
                await page.wait_for_timeout(1000)
                return
        except Exception:
            pass


async def get_card_text_for_link(page, index):
    script = """
    (index) => {
        const links = Array.from(document.querySelectorAll("a[href]"));
        const a = links[index];
        if (!a) return "";

        const candidates = [
            a,
            a.closest("article"),
            a.closest("li"),
            a.closest("[data-testid]"),
            a.parentElement,
            a.parentElement ? a.parentElement.parentElement : null,
            a.parentElement && a.parentElement.parentElement ? a.parentElement.parentElement.parentElement : null
        ];

        let best = "";

        for (const el of candidates) {
            if (!el) continue;
            const txt = (el.innerText || "").replace(/\\s+/g, " ").trim();
            if (txt.length > best.length) best = txt;
        }

        return best;
    }
    """

    try:
        text = await page.evaluate(script, index)
        return clean_text(text)
    except Exception:
        return ""


async def get_all_links_with_context(page):
    result = []

    links = await page.locator("a[href]").all()

    for i, link in enumerate(links):
        try:
            href = await link.get_attribute("href")
            if not href:
                continue

            url = normalize_url(href)

            if not is_real_ad_url(url):
                continue

            link_text = ""
            try:
                link_text = clean_text(await link.inner_text(timeout=1000))
            except Exception:
                pass

            card_text = await get_card_text_for_link(page, i)

            result.append({
                "url": url,
                "link_text": link_text,
                "card_text": card_text,
            })

        except Exception:
            continue

    return result


async def collect_ad_links(page, search):
    candidates = []
    seen = set()

    query = search["query"]

    for page_num in range(1, MAX_SEARCH_PAGES + 1):
        params = {
            "q": query,
            "page": page_num,
        }

        search_url = f"{BASE_URL}?{urlencode(params)}"
        print(f"Hämtar söksida {page_num} för {search['display_name']}: {search_url}")

        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(SEARCH_PAGE_DELAY_MS)
            await accept_cookies(page)
            await page.wait_for_timeout(500)
        except Exception as e:
            print(f"Kunde inte öppna söksida {page_num}: {e}")
            continue

        links = await get_all_links_with_context(page)
        print(f"Hittade {len(links)} riktiga annonslänkar på söksida {page_num}.")

        found_this_page = 0

        for item in links:
            url = item["url"]
            card_text = item["card_text"]
            link_text = item["link_text"]
            combined = clean_text(f"{link_text} {card_text} {url}")

            if url in seen:
                continue

            if not is_real_ad_url(url):
                continue

            if not text_looks_like_car_card(combined):
                continue

            seen.add(url)

            candidates.append({
                "url": url,
                "search_text": combined[:1000],
                "search_page": page_num,
                "search_query": query,
                "make": search["make"],
                "model": search["model"],
                "variant": search["variant"],
                "display_name": search["display_name"],
                "required_terms": "|".join(search["required_terms"]),
            })

            found_this_page += 1

        print(f"Sparade {found_this_page} kandidat-länkar från söksida {page_num}.")

        await page.wait_for_timeout(1000)

    return candidates


async def get_page_title(page):
    selectors = [
        "h1",
        "[data-testid='ad-title']",
        "[data-cy='ad-title']",
    ]

    for selector in selectors:
        try:
            count = await page.locator(selector).count()
            if count == 0:
                continue

            text = clean_text(await page.locator(selector).first.inner_text(timeout=3000))

            if text:
                return text
        except Exception:
            pass

    try:
        return clean_text(await page.title())
    except Exception:
        return ""


async def get_body_text(page):
    try:
        return clean_text(await page.locator("body").inner_text(timeout=8000))
    except Exception:
        return ""


async def scrape_detail_page(page, candidate):
    url = candidate["url"]

    if not is_real_ad_url(url):
        return None

    search = {
        "make": candidate["make"],
        "model": candidate["model"],
        "variant": candidate["variant"],
        "display_name": candidate["display_name"],
        "required_terms": candidate["required_terms"].split("|"),
    }

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(DETAIL_PAGE_DELAY_MS)
        await accept_cookies(page)
    except Exception as e:
        print(f"Kunde inte öppna annons: {url} | {e}")
        return None

    title = await get_page_title(page)
    body_text = await get_body_text(page)

    combined_text = clean_text(f"{title} {body_text} {candidate.get('search_text', '')}")

    if not detail_text_is_relevant(combined_text, url, search):
        return None

    price = parse_price(combined_text)
    year = parse_year(combined_text)
    mileage_km = parse_mileage_km(combined_text)

    if price is None or year is None or mileage_km is None:
        return None

    row = {
        "scraped_at": datetime.now().isoformat(timespec="seconds"),
        "make": candidate["make"],
        "model": candidate["model"],
        "variant": candidate["variant"],
        "display_name": candidate["display_name"],
        "title_text": title,
        "url": url,
        "price_sek": price,
        "year": year,
        "mileage_km": mileage_km,
        "source": "market",
        "status": "active_or_seen",
    }

    return row


def save_rows(rows):
    fieldnames = [
        "scraped_at",
        "make",
        "model",
        "variant",
        "display_name",
        "title_text",
        "url",
        "price_sek",
        "year",
        "mileage_km",
        "source",
        "status",
    ]

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


async def scrape():
    rows = []
    seen_detail_keys = set()
    debug_candidates = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0 Safari/537.36"
            ),
            viewport={"width": 1400, "height": 1000},
        )

        search_page = await context.new_page()
        detail_page = await context.new_page()

        all_candidates = []

        for search in SEARCHES:
            candidates = await collect_ad_links(search_page, search)
            all_candidates.extend(candidates)
            debug_candidates.extend(candidates)

        with open(DEBUG_LINKS_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "url",
                    "search_page",
                    "search_query",
                    "make",
                    "model",
                    "variant",
                    "display_name",
                    "required_terms",
                    "search_text",
                ],
            )
            writer.writeheader()
            writer.writerows(debug_candidates)

        print("")
        print(f"Totalt antal kandidat-länkar: {len(all_candidates)}")
        print("Börjar öppna varje kandidat en i taget.")
        print("")

        max_total_detail_pages = MAX_DETAIL_PAGES_PER_SEARCH * len(SEARCHES)

        for index, candidate in enumerate(all_candidates[:max_total_detail_pages], start=1):
            url = candidate["url"]
            key = f"{url}|{candidate['display_name']}"

            if key in seen_detail_keys:
                continue

            seen_detail_keys.add(key)

            print(f"[{index}/{min(len(all_candidates), max_total_detail_pages)}] Öppnar: {url}")

            row = await scrape_detail_page(detail_page, candidate)

            if row is None:
                print("Ej relevant eller kunde inte läsa komplett annonsdata.")
            else:
                rows.append(row)
                save_rows(rows)

                print(
                    "SPARAD:",
                    row.get("display_name"),
                    "pris=", row.get("price_sek"),
                    "år=", row.get("year"),
                    "km=", row.get("mileage_km"),
                    "titel=", row.get("title_text"),
                )

            await detail_page.wait_for_timeout(BETWEEN_DETAILS_DELAY_MS)

        await browser.close()

    save_rows(rows)

    print("")
    print(f"Klart. Sparade {len(rows)} annonser i {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(scrape())

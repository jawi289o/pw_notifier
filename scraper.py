import time
import random
import requests
from bs4 import BeautifulSoup
from config import (
    USER_AGENTS,
    REQUEST_DELAY_MIN,
    REQUEST_DELAY_MAX,
    INCLUDE_FEATURED,
    MAX_PAGES,
)

# ============================================================
# Session setup — mimics a real browser visit
# ============================================================
# We use a persistent requests.Session so cookies are carried
# across requests (just like a real browser would do).
# We visit the homepage first to pick up session cookies,
# then use those cookies for all subsequent requests.

def _build_session() -> requests.Session:
    """
    Create a requests Session that looks like a real browser:
      - Random User-Agent chosen per session
      - Full Chrome-like headers including sec-fetch-* and sec-ch-ua
      - Visits PakWheels homepage first to collect session cookies
      - Random startup delay to avoid robotic exact-on-the-minute hits
    """
    ua = random.choice(USER_AGENTS)
    is_chrome = "Chrome" in ua and "Edg" not in ua
    is_edge   = "Edg" in ua
    is_ff     = "Firefox" in ua

    session = requests.Session()

    # Build realistic headers matching the chosen browser
    if is_chrome or is_edge:
        browser_name    = "Chromium"
        browser_version = ua.split("Chrome/")[1].split(".")[0]
        brand           = '"Microsoft Edge"' if is_edge else '"Google Chrome"'
        sec_ch_ua = (
            f'"{browser_name}";v="{browser_version}", '
            f'{brand};v="{browser_version}", '
            '"Not-A.Brand";v="99"'
        )
        session.headers.update({
            "User-Agent":                ua,
            "Accept":                    "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language":           "en-US,en;q=0.9",
            "Accept-Encoding":           "gzip, deflate, br",
            "sec-ch-ua":                 sec_ch_ua,
            "sec-ch-ua-mobile":          "?0",
            "sec-ch-ua-platform":        '"Windows"' if "Windows" in ua else '"macOS"',
            "sec-fetch-dest":            "document",
            "sec-fetch-mode":            "navigate",
            "sec-fetch-site":            "none",
            "sec-fetch-user":            "?1",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control":             "max-age=0",
            "Connection":                "keep-alive",
        })
    else:
        # Firefox headers
        session.headers.update({
            "User-Agent":                ua,
            "Accept":                    "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language":           "en-US,en;q=0.5",
            "Accept-Encoding":           "gzip, deflate, br",
            "sec-fetch-dest":            "document",
            "sec-fetch-mode":            "navigate",
            "sec-fetch-site":            "none",
            "sec-fetch-user":            "?1",
            "Upgrade-Insecure-Requests": "1",
            "Connection":                "keep-alive",
        })

    # Random startup delay (0–90 seconds) so the job doesn't always
    # fire at the exact same second each run — looks more human
    startup_delay = random.randint(0, 90)
    print(f"[scraper] Startup delay: {startup_delay}s  |  UA: {ua[:60]}...")
    time.sleep(startup_delay)

    # Visit homepage first to get session cookies
    try:
        print("[scraper] Visiting homepage to collect session cookies...")
        session.get("https://www.pakwheels.com/", timeout=20)
        # Small pause after homepage — like a human reading it briefly
        time.sleep(random.uniform(2, 5))
    except Exception as e:
        print(f"[scraper] Homepage visit failed (non-fatal): {e}")

    return session


# Module-level session — created once per script run
_SESSION = _build_session()


def _human_delay(min_s: float = None, max_s: float = None):
    """Sleep for a random duration between min_s and max_s seconds."""
    lo = min_s if min_s is not None else REQUEST_DELAY_MIN
    hi = max_s if max_s is not None else REQUEST_DELAY_MAX
    delay = random.uniform(lo, hi)
    print(f"[scraper] Waiting {delay:.1f}s...")
    time.sleep(delay)


def get_soup(url: str, referer: str = "https://www.pakwheels.com/") -> BeautifulSoup | None:
    """
    Fetch a URL using the persistent session and return a BeautifulSoup.
    Updates the Referer header to simulate natural navigation.
    Returns None on failure.
    """
    _SESSION.headers["Referer"]        = referer
    _SESSION.headers["sec-fetch-site"] = "same-origin"

    try:
        resp = _SESSION.get(url, timeout=20)
        resp.raise_for_status()

        # Detect if we've been served a CAPTCHA or block page
        if "captcha" in resp.text.lower() or "blocked" in resp.text.lower():
            print(f"[scraper] WARNING: Possible block/CAPTCHA detected at {url}")
            return None

        return BeautifulSoup(resp.text, "lxml")

    except requests.exceptions.HTTPError as e:
        print(f"[scraper] HTTP error {e.response.status_code} for {url}")
        return None
    except Exception as e:
        print(f"[scraper] Failed to fetch {url}: {e}")
        return None


# ============================================================
# Parsing helpers
# ============================================================

def parse_search_page(soup: BeautifulSoup) -> list[dict]:
    """
    Extract basic listing info from the search results page.
    Returns a list of dicts with keys:
        url, title, price, city, year, mileage,
        fuel, cc, transmission, is_featured
    """
    listings = []
    cards = soup.select("li.classified-listing")

    for card in cards:
        is_featured = "featured-listing" in card.get("class", [])

        if not INCLUDE_FEATURED and is_featured:
            continue

        # URL & Title
        anchor = card.select_one("a.car-name.ad-detail-path")
        if not anchor:
            continue
        relative_url = anchor.get("href", "")
        url = (
            f"https://www.pakwheels.com{relative_url}"
            if relative_url.startswith("/")
            else relative_url
        )
        title_tag = anchor.select_one("h3")
        title = title_tag.get_text(strip=True) if title_tag else "N/A"

        # Price
        price_tag = card.select_one("div.price-details")
        price = price_tag.get_text(strip=True) if price_tag else "N/A"

        # City
        city_tag = card.select_one("ul.search-vehicle-info li")
        city = city_tag.get_text(strip=True) if city_tag else "N/A"

        # Year / Mileage / Fuel / CC / Transmission
        specs        = card.select("ul.search-vehicle-info-2 li")
        year         = specs[0].get_text(strip=True) if len(specs) > 0 else "N/A"
        mileage      = specs[1].get_text(strip=True) if len(specs) > 1 else "N/A"
        fuel         = specs[2].get_text(strip=True) if len(specs) > 2 else "N/A"
        cc           = specs[3].get_text(strip=True) if len(specs) > 3 else "N/A"
        transmission = specs[4].get_text(strip=True) if len(specs) > 4 else "N/A"

        listings.append({
            "url":          url,
            "title":        title,
            "price":        price,
            "city":         city,
            "year":         year,
            "mileage":      mileage,
            "fuel":         fuel,
            "cc":           cc,
            "transmission": transmission,
            "is_featured":  is_featured,
        })

    return listings


def parse_listing_page(url: str, referer: str) -> dict:
    """
    Fetch an individual car listing page and extract:
        seller_name, registered_in, color, seller_comments
    Uses a human-like random delay before each request.
    """
    result = {
        "seller_name":     "",
        "registered_in":   "",
        "color":           "",
        "seller_comments": "",
    }

    _human_delay()
    soup = get_soup(url, referer=referer)
    if not soup:
        return result

    # Seller name
    seller_tag = soup.select_one(".owner-details h5.nomargin")
    if seller_tag:
        result["seller_name"] = seller_tag.get_text(strip=True)

    # Registered In / Color from ul.ul-featured
    feature_items = soup.select("ul.ul-featured li")
    i = 0
    while i < len(feature_items) - 1:
        label = feature_items[i].get_text(strip=True).lower()
        value = feature_items[i + 1].get_text(strip=True)
        if "registered" in label:
            result["registered_in"] = value
        elif "color" in label:
            result["color"] = value
        i += 2

    # Seller comments
    comments_heading = soup.find("h2", id="scroll_seller_comments")
    if comments_heading:
        comments_div = comments_heading.find_next_sibling("div")
        if comments_div:
            for tag in comments_div.select("label"):
                tag.decompose()
            result["seller_comments"] = comments_div.get_text(separator=" ", strip=True)

    return result


def scrape_all_listings(search_url: str) -> list[dict]:
    """
    Scrape the search page (up to MAX_PAGES) and return
    a list of basic listing dicts.
    """
    all_listings = []

    for page in range(1, MAX_PAGES + 1):
        url = search_url if page == 1 else f"{search_url}?page={page}"
        print(f"[scraper] Fetching search page {page}: {url}")

        referer = "https://www.pakwheels.com/used-cars/" if page == 1 else search_url
        soup = get_soup(url, referer=referer)

        if not soup:
            break

        listings = parse_search_page(soup)
        if not listings:
            print(f"[scraper] No listings on page {page}, stopping.")
            break

        all_listings.extend(listings)
        print(f"[scraper] Found {len(listings)} listings on page {page}")

        # Pause between pages like a human would
        if page < MAX_PAGES:
            _human_delay(3, 7)

    return all_listings

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


def _build_session() -> requests.Session:
    """
    Create a requests Session that looks like a real browser.
    Visits PakWheels homepage first to collect session cookies.
    """
    ua = random.choice(USER_AGENTS)
    is_ff = "Firefox" in ua

    session = requests.Session()

    # NOTE: We deliberately omit Accept-Encoding so requests handles
    # decompression automatically — avoids garbled gzip/brotli responses
    if not is_ff:
        browser_version = ua.split("Chrome/")[1].split(".")[0]
        is_edge = "Edg" in ua
        brand = '"Microsoft Edge"' if is_edge else '"Google Chrome"'
        sec_ch_ua = (
            f'"Chromium";v="{browser_version}", '
            f'{brand};v="{browser_version}", '
            '"Not-A.Brand";v="99"'
        )
        session.headers.update({
            "User-Agent":                ua,
            "Accept":                    "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language":           "en-US,en;q=0.9",
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
        session.headers.update({
            "User-Agent":                ua,
            "Accept":                    "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language":           "en-US,en;q=0.5",
            "sec-fetch-dest":            "document",
            "sec-fetch-mode":            "navigate",
            "sec-fetch-site":            "none",
            "sec-fetch-user":            "?1",
            "Upgrade-Insecure-Requests": "1",
            "Connection":                "keep-alive",
        })

    # Random startup delay (0–60s)
    startup_delay = random.randint(0, 60)
    print(f"[scraper] Startup delay: {startup_delay}s  |  UA: {ua[:60]}...")
    time.sleep(startup_delay)

    # Visit homepage first to get session cookies
    try:
        print("[scraper] Visiting homepage to collect session cookies...")
        resp = session.get(
            "https://www.pakwheels.com/",
            timeout=20,
            stream=False
        )
        print(f"[scraper] Homepage status: {resp.status_code} | Encoding: {resp.encoding}")
        time.sleep(random.uniform(2, 4))
    except Exception as e:
        print(f"[scraper] Homepage visit failed (non-fatal): {e}")

    return session


_SESSION = _build_session()


def _human_delay(min_s: float = None, max_s: float = None):
    lo = min_s if min_s is not None else REQUEST_DELAY_MIN
    hi = max_s if max_s is not None else REQUEST_DELAY_MAX
    delay = random.uniform(lo, hi)
    print(f"[scraper] Waiting {delay:.1f}s...")
    time.sleep(delay)


def get_soup(url: str, referer: str = "https://www.pakwheels.com/") -> BeautifulSoup | None:
    _SESSION.headers["Referer"]        = referer
    _SESSION.headers["sec-fetch-site"] = "same-origin"

    try:
        resp = _SESSION.get(url, timeout=20, stream=False)
        print(f"[scraper] GET {url} → status {resp.status_code} | encoding: {resp.encoding} | size: {len(resp.text)} chars")

        resp.raise_for_status()

        # Use resp.text which requests decodes properly
        html = resp.text

        # Debug: show page title area
        if "<title>" in html:
            start = html.find("<title>")
            end   = html.find("</title>", start)
            print(f"[scraper] Page title: {html[start:end+8]}")
        else:
            print("[scraper] No <title> tag found in response")

        if "captcha" in html.lower() or "blocked" in html.lower():
            print("[scraper] WARNING: Possible block/CAPTCHA detected")
            return None

        return BeautifulSoup(html, "lxml")

    except requests.exceptions.HTTPError as e:
        print(f"[scraper] HTTP error {e.response.status_code} for {url}")
        return None
    except Exception as e:
        print(f"[scraper] Failed to fetch {url}: {e}")
        return None


def parse_search_page(soup: BeautifulSoup) -> list[dict]:
    listings = []

    cards = soup.select("li.classified-listing")
    print(f"[scraper] Cards found: {len(cards)}")

    # Try fallback selector
    if not cards:
        cards = soup.select("li[data-listing-id]")
        print(f"[scraper] Fallback cards found: {len(cards)}")

    for card in cards:
        is_featured = "featured-listing" in card.get("class", [])

        if not INCLUDE_FEATURED and is_featured:
            continue

        anchor = card.select_one("a.car-name.ad-detail-path")
        if not anchor:
            anchor = card.select_one("a[href*='/used-cars/']")
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

        price_tag = card.select_one("div.price-details")
        price = price_tag.get_text(strip=True) if price_tag else "N/A"

        city_tag = card.select_one("ul.search-vehicle-info li")
        city = city_tag.get_text(strip=True) if city_tag else "N/A"

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

    seller_tag = soup.select_one(".owner-details h5.nomargin")
    if seller_tag:
        result["seller_name"] = seller_tag.get_text(strip=True)

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

    comments_heading = soup.find("h2", id="scroll_seller_comments")
    if comments_heading:
        comments_div = comments_heading.find_next_sibling("div")
        if comments_div:
            for tag in comments_div.select("label"):
                tag.decompose()
            result["seller_comments"] = comments_div.get_text(separator=" ", strip=True)

    return result


def scrape_all_listings(search_url: str) -> list[dict]:
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

        if page < MAX_PAGES:
            _human_delay(3, 7)

    return all_listings

"""
PakWheels Scraper — Main Entry Point
=====================================
Flow:
  1. Load seen seller usernames from GitHub Gist
  2. Scrape search results page
  3. For each listing not seen before:
       a. Open individual listing page (with correct Referer header)
       b. Get seller name, color, registered in, comments
       c. Check seller name against seen list (duplicate check)
       d. If new → send Discord notification → mark seller as seen
  4. Save updated seen list back to Gist
"""

from config     import SEARCH_URL
from scraper    import scrape_all_listings, parse_listing_page
from notifier   import send_discord_notification
from gist_store import load_seen, save_seen


def main():
    print("=" * 60)
    print("PakWheels Scraper Starting")
    print(f"Search URL: {SEARCH_URL}")
    print("=" * 60)

    # Step 1 — Load already-seen sellers
    seen = load_seen()
    print(f"[main] Loaded {len(seen)} seen seller(s) from Gist")

    # Step 2 — Scrape search page
    listings = scrape_all_listings(SEARCH_URL)
    print(f"[main] Total listings found: {len(listings)}")

    if not listings:
        print("[main] No listings found. Exiting.")
        return

    # Step 3 — Process each listing
    new_count = 0
    updated   = False

    for listing in listings:
        print(f"[main] Checking: {listing['url']}")

        # Pass the search page URL as Referer — looks like natural navigation
        details = parse_listing_page(listing["url"], referer=SEARCH_URL)
        listing.update(details)

        seller_name = details.get("seller_name", "").strip()

        if not seller_name:
            print(f"[main] Could not find seller name, skipping.")
            continue

        # Duplicate check
        if seller_name in seen:
            print(f"[main] Already seen seller '{seller_name}', skipping.")
            continue

        # New listing — notify
        print(f"[main] NEW listing from '{seller_name}': {listing['title']}")
        success = send_discord_notification(listing)

        if success:
            seen.add(seller_name)
            updated = True
            new_count += 1

    # Step 4 — Save updated seen list
    if updated:
        save_seen(seen)
        print(f"[main] Saved {len(seen)} seller(s) to Gist")

    print("=" * 60)
    print(f"Done. {new_count} new listing(s) notified.")
    print("=" * 60)


if __name__ == "__main__":
    main()

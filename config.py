# ============================================================
# PakWheels Scraper Configuration
# ============================================================
# Replace the SEARCH_URL with your own search URL from PakWheels
# Just go to pakwheels.com, filter what you want, copy the URL

SEARCH_URL = "https://www.pakwheels.com/used-cars/search/-/mk_toyota/md_vitz/yr_2014_2016/"

# How many pages to scrape (1 = first 24 listings only, recommended)
MAX_PAGES = 1

# Include featured ads? (True = yes, False = skip featured ads)
INCLUDE_FEATURED = True

# Delay between individual listing page requests — randomised in scraper
# These are the min/max bounds in seconds
REQUEST_DELAY_MIN = 4
REQUEST_DELAY_MAX = 9

# Rotating User-Agent strings — real Chrome/Firefox/Edge on Windows & Mac
# The scraper picks one randomly each session
USER_AGENTS = [
    # Chrome 124 Windows
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    # Chrome 123 Mac
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    # Firefox 125 Windows
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) "
        "Gecko/20100101 Firefox/125.0"
    ),
    # Firefox 124 Mac
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:124.0) "
        "Gecko/20100101 Firefox/124.0"
    ),
    # Edge 124 Windows
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0"
    ),
    # Chrome 122 Linux
    (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
]

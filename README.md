# PakWheels Car Notifier

Scrapes PakWheels used car listings and sends Discord notifications for new listings.
Runs automatically every 15 minutes via GitHub Actions — completely free.

## Files

| File | Purpose |
|---|---|
| `config.py` | Your search URL and settings — **edit this** |
| `scraper.py` | Parses search page and individual listing pages |
| `notifier.py` | Sends Discord embed notifications |
| `gist_store.py` | Reads/writes seen sellers to GitHub Gist |
| `main.py` | Main entry point — ties everything together |
| `.github/workflows/scrape.yml` | GitHub Actions schedule |

## Setup

### 1. GitHub Secrets Required

Go to your repo → **Settings → Secrets and variables → Actions** and add:

| Secret | Value |
|---|---|
| `DISCORD_BOT_TOKEN` | Your Discord bot token |
| `DISCORD_CHANNEL_ID` | Your Discord channel ID |
| `GIST_TOKEN` | GitHub personal access token (gist scope) |
| `GIST_ID` | ID of your private Gist (the long hash in the URL) |

### 2. Edit config.py

Change `SEARCH_URL` to your own PakWheels search URL:

```python
SEARCH_URL = "https://www.pakwheels.com/used-cars/search/-/mk_toyota/md_vitz/yr_2014_2016/"
```

### 3. Push to GitHub

```bash
git add .
git commit -m "Initial setup"
git push
```

### 4. Test manually

Go to **Actions tab → PakWheels Scraper → Run workflow**

## How duplicate detection works

The scraper stores seller usernames in a private GitHub Gist.
If a seller deletes and reposts their car, the same username is detected
and the notification is skipped — no spam.

## Discord message format

Each notification shows:
- Title + Featured/New badge
- Price, City, Year, Mileage, Fuel, CC, Transmission
- Registered In, Color, Seller name
- Seller's comments
- Direct link to the listing

import os
import json
import requests

# ============================================================
# GitHub Gist Storage for Seen Usernames (Duplicate Tracking)
# ============================================================
# Reads/writes a JSON array of seen seller usernames
# stored in a private GitHub Gist.
# Env vars required: GIST_TOKEN, GIST_ID

GIST_TOKEN = os.environ.get("GIST_TOKEN")
GIST_ID    = os.environ.get("GIST_ID")
FILENAME   = "seen_urls.json"   # filename inside the Gist


def _headers():
    return {
        "Authorization": f"token {GIST_TOKEN}",
        "Accept": "application/vnd.github+json",
    }


def load_seen() -> set:
    """Return the set of already-seen seller usernames from the Gist."""
    url = f"https://api.github.com/gists/{GIST_ID}"
    try:
        resp = requests.get(url, headers=_headers(), timeout=15)
        resp.raise_for_status()
        content = resp.json()["files"][FILENAME]["content"]
        return set(json.loads(content))
    except Exception as e:
        print(f"[gist] Failed to load seen list: {e}")
        return set()


def save_seen(seen: set) -> bool:
    """Persist the updated set of seen seller usernames back to the Gist."""
    url = f"https://api.github.com/gists/{GIST_ID}"
    payload = {
        "files": {
            FILENAME: {
                "content": json.dumps(list(seen), ensure_ascii=False, indent=2)
            }
        }
    }
    try:
        resp = requests.patch(url, headers=_headers(), json=payload, timeout=15)
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"[gist] Failed to save seen list: {e}")
        return False

import os
import requests

# ============================================================
# Discord Notifier
# ============================================================
# Sends a formatted embed message to your Discord channel.
# Env vars required: DISCORD_BOT_TOKEN, DISCORD_CHANNEL_ID

DISCORD_BOT_TOKEN  = os.environ.get("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = os.environ.get("DISCORD_CHANNEL_ID")

API_URL = f"https://discord.com/api/v10/channels/{DISCORD_CHANNEL_ID}/messages"


def send_discord_notification(listing: dict) -> bool:
    """
    Send a Discord embed message for a new car listing.
    listing dict keys: url, title, price, city, year, mileage,
                       fuel, cc, transmission, is_featured,
                       seller_name, registered_in, color, seller_comments
    Returns True on success.
    """
    badge     = "⭐ FEATURED" if listing.get("is_featured") else "🆕 NEW LISTING"
    seller    = listing.get("seller_name", "Unknown")
    reg_in    = listing.get("registered_in", "N/A")
    color     = listing.get("color", "N/A")
    comments  = listing.get("seller_comments", "")

    # Truncate comments to fit Discord embed limits
    if comments and len(comments) > 300:
        comments = comments[:297] + "..."

    # Build embed fields
    fields = [
        {"name": "💰 Price",        "value": listing.get("price", "N/A"),        "inline": True},
        {"name": "📍 City",         "value": listing.get("city", "N/A"),         "inline": True},
        {"name": "📅 Year",         "value": listing.get("year", "N/A"),         "inline": True},
        {"name": "🛣️ Mileage",      "value": listing.get("mileage", "N/A"),      "inline": True},
        {"name": "⛽ Fuel",         "value": listing.get("fuel", "N/A"),         "inline": True},
        {"name": "⚙️ Transmission", "value": listing.get("transmission", "N/A"), "inline": True},
        {"name": "🔧 Engine",       "value": listing.get("cc", "N/A"),           "inline": True},
        {"name": "🏙️ Registered",   "value": reg_in,                             "inline": True},
        {"name": "🎨 Color",        "value": color,                              "inline": True},
        {"name": "👤 Seller",       "value": seller,                             "inline": True},
    ]

    if comments:
        fields.append({"name": "💬 Seller Comments", "value": comments, "inline": False})

    embed = {
        "title":       f"{badge}  |  {listing.get('title', 'Car Listing')}",
        "url":         listing.get("url", ""),
        "color":       0x00b300 if not listing.get("is_featured") else 0xf5a623,
        "fields":      fields,
        "footer":      {"text": "PakWheels Notifier • pakwheels.com"},
    }

    payload = {"embeds": [embed]}
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type":  "application/json",
    }

    try:
        resp = requests.post(API_URL, json=payload, headers=headers, timeout=15)
        if resp.status_code in (200, 201, 204):
            print(f"[notifier] Sent notification for: {listing.get('title')}")
            return True
        else:
            print(f"[notifier] Discord API error {resp.status_code}: {resp.text}")
            return False
    except Exception as e:
        print(f"[notifier] Failed to send notification: {e}")
        return False

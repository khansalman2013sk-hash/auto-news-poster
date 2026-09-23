"""
upload_facebook.py
Posts a video to a Facebook PAGE using the official Graph API.

IMPORTANT: Meta does not allow automated posting to a personal profile —
only to a Page you manage. This is why the bot needs a Facebook Page (free
and easy to create) rather than your personal timeline. See README for how
to create one and get a long-lived Page access token.

Needs these environment variables (set as GitHub Secrets for automation):
  FB_PAGE_ID            — your Facebook Page's numeric ID
  FB_PAGE_ACCESS_TOKEN  — a long-lived Page access token
"""
import os

import requests

GRAPH_VERSION = "v19.0"


def upload_video(file_path, description=""):
    page_id = os.environ["FB_PAGE_ID"]
    token = os.environ["FB_PAGE_ACCESS_TOKEN"]
    url = f"https://graph-video.facebook.com/{GRAPH_VERSION}/{page_id}/videos"

    with open(file_path, "rb") as f:
        resp = requests.post(
            url,
            data={"access_token": token, "description": description[:5000]},
            files={"source": f},
            timeout=600,
        )
    resp.raise_for_status()
    result = resp.json()
    print(f"  Facebook post id: {result.get('id')}")
    return result.get("id")

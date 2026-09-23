"""
upload_youtube.py
Uploads a video to YouTube using the official YouTube Data API v3.

FIRST-TIME SETUP (one time, on your own laptop — needs a browser, see README):
    python src/upload_youtube.py --auth
This opens a Google login page, asks you to allow access to your channel,
then saves a token.json file. After that, uploads run with no browser
needed — that's what the GitHub Actions automation uses.

QUOTA NOTE: a video upload costs 1600 units; the free daily quota is
10,000 units — so about 6 uploads/day total (long-form + Shorts combined)
on the default quota. Plan `top_n` / schedule in config.yaml accordingly.
"""
import argparse
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_FILE = "token.json"
CLIENT_SECRET_FILE = "client_secret.json"  # downloaded from Google Cloud Console — see README


def _get_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds


def upload_video(file_path, title, description, tags=None, category_id="25",
                  privacy_status="public", is_short=False):
    """category_id 25 = "News & Politics". Full list in the YouTube API docs."""
    creds = _get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    if is_short and "#Shorts" not in title:
        title = f"{title} #Shorts"

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags or [],
            "categoryId": category_id,
        },
        "status": {"privacyStatus": privacy_status},
    }
    media = MediaFileUpload(file_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  upload progress: {int(status.progress() * 100)}%")
    print(f"  uploaded: https://youtu.be/{response['id']}")
    return response["id"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--auth", action="store_true", help="run the one-time browser login")
    args = parser.parse_args()
    if args.auth:
        _get_credentials()
        print(f"Saved {TOKEN_FILE}.")
        print("Copy its FULL contents into a GitHub secret named YOUTUBE_TOKEN_JSON (see README).")

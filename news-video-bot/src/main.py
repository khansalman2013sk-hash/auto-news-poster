"""
main.py — runs the full pipeline once:
    fetch news -> build script -> build video(s) -> upload to YouTube/Facebook

Run manually:     python src/main.py
Run on schedule:  see .github/workflows/daily-news-bot.yml (free, via GitHub Actions)
"""
import os
import sys
import traceback
from datetime import datetime

import yaml

sys.path.insert(0, os.path.dirname(__file__))
from fetch_news import fetch_top_news          # noqa: E402
from generate_script import build_script       # noqa: E402
from make_video import build_video             # noqa: E402


def load_config(path="config.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    cfg = load_config()
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    work_dir = os.path.join("output", run_id)
    os.makedirs(work_dir, exist_ok=True)

    print(f"[1/4] Fetching top {cfg['top_n']} news...")
    items = fetch_top_news(cfg["rss_feeds"], top_n=cfg["top_n"])
    if not items:
        print("No news items fetched — check the RSS feed URLs in config.yaml. Stopping.")
        return
    print(f"  got {len(items)} items")

    print("[2/4] Building narration script...")
    script = build_script(items, mode=cfg.get("script_mode", "template"))

    title = f"Top {len(items)} News Update - {datetime.now().strftime('%d %b %Y')}"
    description = "\n".join(f"{i + 1}. {it['title']} (Source: {it['source']})" for i, it in enumerate(items))
    description += "\n\nAutomated news roundup. Full stories:\n"
    description += "\n".join(it["link"] for it in items if it.get("link"))

    print("[3/4] Building video(s)...")
    long_path = os.path.join(work_dir, "long.mp4")
    build_video(items, script, cfg, work_dir, long_path, vertical=False)
    print(f"  long-form video ready: {long_path}")

    short_path = None
    if cfg["video"].get("make_shorts"):
        short_path = os.path.join(work_dir, "short.mp4")
        build_video(items, script, cfg, work_dir, short_path, vertical=True, max_items=3)
        print(f"  shorts video ready: {short_path}")

    print("[4/4] Publishing...")
    pub = cfg.get("publish", {})

    if pub.get("youtube"):
        try:
            from upload_youtube import upload_video as yt_upload
            yt_upload(long_path, title, description, privacy_status=pub.get("privacy_status", "public"))
        except Exception:
            print("  YouTube (long-form) upload failed:")
            traceback.print_exc()

    if pub.get("youtube_shorts") and short_path:
        try:
            from upload_youtube import upload_video as yt_upload
            yt_upload(short_path, title, description, privacy_status=pub.get("privacy_status", "public"), is_short=True)
        except Exception:
            print("  YouTube (Shorts) upload failed:")
            traceback.print_exc()

    if pub.get("facebook"):
        try:
            from upload_facebook import upload_video as fb_upload
            fb_upload(long_path, description=description)
        except Exception:
            print("  Facebook upload failed:")
            traceback.print_exc()

    print("Done.")


if __name__ == "__main__":
    main()

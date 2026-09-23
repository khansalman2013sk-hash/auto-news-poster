"""
make_video.py
Builds an MP4 video from the narration script:
  1. Synthesizes TTS audio per line (edge-tts — free).
  2. Draws a "news card" image per line (Pillow) with the headline + index.
  3. Combines image+audio into a clip per item (moviepy), concatenates with
     an intro/outro card, exports the final video.
  4. Can also build a short vertical (9:16) cut using only the first few
     items, sized for YouTube Shorts / Facebook Reels.
"""
import asyncio
import os
import textwrap

import edge_tts
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips


def _load_fonts(font_path, size):
    try:
        title_font = ImageFont.truetype(font_path, size=int(size[1] * 0.06))
        small_font = ImageFont.truetype(font_path, size=int(size[1] * 0.03))
    except Exception:
        # Font file missing/unreadable — falls back to a basic font.
        # NOTE: the basic fallback font cannot render Hindi (Devanagari) text
        # correctly. See README "Add a Hindi font" step.
        title_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    return title_font, small_font


def _draw_card(text, index, total, size, bg_color, accent_color, font_path, out_path, source=""):
    img = Image.new("RGB", size, bg_color)
    draw = ImageDraw.Draw(img)
    title_font, small_font = _load_fonts(font_path, size)

    # accent bar at the top
    draw.rectangle([0, 0, size[0], int(size[1] * 0.015)], fill=accent_color)

    # index badge
    draw.text((size[0] * 0.05, size[1] * 0.08), f"{index}/{total}", font=small_font, fill=accent_color)

    # wrapped headline text, roughly centered vertically
    wrap_width = 28 if size[0] < size[1] else 42  # narrower wrap for vertical videos
    wrapped = textwrap.fill(text, width=wrap_width)
    draw.multiline_text((size[0] * 0.08, size[1] * 0.35), wrapped, font=title_font, fill="white", spacing=14)

    if source:
        draw.text((size[0] * 0.08, size[1] * 0.9), f"Source: {source}", font=small_font, fill="#BBBBBB")

    img.save(out_path)


async def _tts_to_file(text, voice, out_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(out_path)


def _synth(text, voice, out_path):
    asyncio.run(_tts_to_file(text, voice, out_path))


def build_video(items, script, cfg, work_dir, out_path, vertical=False, max_items=None):
    """
    items:  list of news dicts (title/source/link/...)
    script: {"intro","outro","lines":[...]}  — same order/length as items
    cfg:    the loaded config.yaml dict
    Returns: out_path
    """
    os.makedirs(work_dir, exist_ok=True)
    vcfg = cfg["video"]
    size = tuple(vcfg["resolution_shorts"] if vertical else vcfg["resolution_long"])
    voice = cfg["voice"]
    bg = vcfg["background_color"]
    accent = vcfg["accent_color"]
    font_path = vcfg["font_path"]
    tag = "vert" if vertical else "long"

    use_items = items if max_items is None else items[:max_items]
    use_lines = script["lines"] if max_items is None else script["lines"][:max_items]

    clips = []

    # --- intro card ---
    intro_img = os.path.join(work_dir, f"{tag}_intro.png")
    intro_audio = os.path.join(work_dir, f"{tag}_intro.mp3")
    _draw_card(script["intro"], 0, len(use_items), size, bg, accent, font_path, intro_img)
    _synth(script["intro"], voice, intro_audio)
    a = AudioFileClip(intro_audio)
    clips.append(ImageClip(intro_img).set_duration(a.duration).set_audio(a))

    # --- one clip per news item ---
    max_dur = vcfg.get("max_seconds_per_item", 15)
    for i, (item, line) in enumerate(zip(use_items, use_lines), 1):
        img_path = os.path.join(work_dir, f"{tag}_item_{i}.png")
        audio_path = os.path.join(work_dir, f"{tag}_item_{i}.mp3")
        _draw_card(item["title"], i, len(use_items), size, bg, accent, font_path, img_path, source=item.get("source", ""))
        _synth(line, voice, audio_path)
        a = AudioFileClip(audio_path)
        dur = min(a.duration, max_dur)
        clips.append(ImageClip(img_path).set_duration(dur).set_audio(a.subclip(0, dur)))

    # --- outro card ---
    outro_img = os.path.join(work_dir, f"{tag}_outro.png")
    outro_audio = os.path.join(work_dir, f"{tag}_outro.mp3")
    _draw_card(script["outro"], len(use_items) + 1, len(use_items), size, bg, accent, font_path, outro_img)
    _synth(script["outro"], voice, outro_audio)
    a = AudioFileClip(outro_audio)
    clips.append(ImageClip(outro_img).set_duration(a.duration).set_audio(a))

    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(out_path, fps=24, codec="libx264", audio_codec="aac", logger=None)
    return out_path

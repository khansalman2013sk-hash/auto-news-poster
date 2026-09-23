"""
generate_script.py
Turns fetched news items into an ORIGINAL narration script. This never
copies article text verbatim — reusing a publisher's exact wording in your
video would be copyright infringement. Two modes:

  "template" — free, fully offline. Simple Hinglish news-anchor phrasing
               built from the headline + short snippet.
  "ai"       — more natural-sounding narration, rewritten by a free-tier
               Gemini API key (GEMINI_API_KEY env var). Falls back to
               "template" automatically if no key is set or the call fails.
"""
import os

TEMPLATE_OPENERS = [
    "Ab baat karte hain",
    "Agli khabar hai",
    "Ek aur badi khabar —",
    "Charcha mein hai",
    "Sunte hain",
]

INTRO = "Namaskar! Dekhte hain aaj ki top khabarein, ek ke baad ek."
OUTRO = "Yehi thi aaj ki badi khabarein. Video pasand aaye to channel ko follow zaroor karein."


def _template_line(idx, item):
    opener = TEMPLATE_OPENERS[idx % len(TEMPLATE_OPENERS)]
    line = f"{opener} {item['title']}."
    if item.get("summary"):
        line += f" {item['summary']}"
    line += f" Report: {item['source']}."
    return line


def _ai_line(item):
    import google.generativeai as genai
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = (
        "Tum ek Hindi/Hinglish news-anchor ho. Neeche di gayi headline aur "
        "summary ko apne shabdon mein, 2-3 chhoti sentences mein, ek natural "
        "TV-anchor jaisi narration line mein badlo. Headline ya summary ko "
        "shabd-ba-shabd copy mat karo, bas usi khabar ko apne tareeke se "
        "batao. Sirf narration line do, kuch aur nahi.\n\n"
        f"Headline: {item['title']}\nSummary: {item.get('summary', '')}"
    )
    resp = model.generate_content(prompt)
    return resp.text.strip()


def build_script(items, mode="template"):
    """
    Returns: {"intro": str, "outro": str, "lines": [str, ...]}
    One narration line per news item, same order as `items`.
    """
    lines = []
    for idx, item in enumerate(items):
        line = None
        if mode == "ai" and os.environ.get("GEMINI_API_KEY"):
            try:
                line = _ai_line(item)
            except Exception as e:
                print(f"[generate_script] AI mode failed for item {idx} ({e}); using template instead.")
        if not line:
            line = _template_line(idx, item)
        lines.append(line)
    return {"intro": INTRO, "outro": OUTRO, "lines": lines}

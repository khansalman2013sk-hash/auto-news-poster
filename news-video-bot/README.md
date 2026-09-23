# News Video Bot

Automatically fetches top news → converts into a narrated video → posts to
**YouTube (long-form + Shorts)** and a **Facebook Page** — on a free daily
schedule, with **zero ongoing cost** and **no server to pay for or keep on**.

---

## ⚠️ Important — read this before you start

1. **Ye article copy nahi karta.** Poori news article uthake seedha video
   banana copyright infringement hai, aur YouTube/Facebook dono aise content
   ko demonetize ya ban kar dete hain. Ye bot sirf **headline + chhoti
   snippet** (RSS feed se, jo publisher khud is kaam ke liye deता hai) leta
   hai, aur uspar apna **original narration** banata hai (`script_mode:
   template` ya `ai` — dono mein wording apni hoti hai, article ki nahi).

2. **Monetization guarantee nahi hai.** YouTube ki Partner Program policy
   "reused/repetitious content" ko monetize nahi karti — sirf headline padhna
   kaafi nahi hai. Zyada safe/valuable banane ke liye apni analysis/opinion
   bhi jodo (script ko manually edit karke, ya `script_mode: ai` use karke).

3. **Facebook automation sirf Page par chalta hai**, personal profile par
   nahi — Meta ki policy personal-timeline automation allow nahi karti. Isi
   liye README mein Page banane ka step hai.

4. **YouTube free quota = ~6 uploads/day** (long-form + Shorts dono milaake).
   Schedule usi hisaab se rakho.

5. Ye sab **free tools** hain (edge-tts, ffmpeg, moviepy, official YouTube/
   Facebook APIs). Koi paid subscription zaroori nahi. Sirf **ek-baar ka
   setup time** lagega (~1-2 ghante), automatic chalne ke baad kuch nahi
   karna.

---

## Ye kaam kaise karta hai (overview)

```
RSS feeds  -->  original narration script  -->  TTS audio + text-card video
   (free)          (template / free AI)              (edge-tts + moviepy)
                                                              |
                                                              v
                                          YouTube (long + Shorts) + Facebook Page
                                          (official APIs, free)
```

Poora pipeline **GitHub Actions** par chalta hai — ye GitHub ka free
scheduled-runner service hai, jo roz apne aap ek naya container spin-up
karke tumhara script chalata hai. **Tumhara laptop/mobile on rehne ki
zaroorat nahi.**

---

## Files

```
news-video-bot/
├── config.yaml              <- sab settings yahin se badlo
├── requirements.txt
├── src/
│   ├── fetch_news.py        <- RSS se top news
│   ├── generate_script.py   <- original narration banata hai
│   ├── make_video.py        <- TTS + visuals -> MP4
│   ├── upload_youtube.py    <- YouTube par upload
│   ├── upload_facebook.py   <- Facebook Page par upload
│   └── main.py               <- sab jodta hai, ye hi chalega
└── .github/workflows/
    └── daily-news-bot.yml   <- free daily automatic schedule
```

---

## Setup — step by step

### Step 0: Cheezein install karo (sirf one-time, apne laptop par)

```bash
python -m venv venv
source venv/bin/activate        # Windows par: venv\Scripts\activate
pip install -r requirements.txt
```

`ffmpeg` bhi chahiye (video export ke liye):
- **Windows:** [ffmpeg.org](https://ffmpeg.org/download.html) se download karo, PATH mein add karo
- **Mac:** `brew install ffmpeg`
- **Linux:** `sudo apt install ffmpeg`

Hindi text sahi dikhne ke liye `assets/fonts/` folder mein ek Devanagari font
daalo — us folder ke andar `PUT_FONT_HERE.txt` mein poora tarika likha hai
(2 minute ka kaam, Google Fonts se free download).

### Step 1: YouTube API credentials banao

1. [Google Cloud Console](https://console.cloud.google.com/) par jaao, naya
   project banao.
2. "APIs & Services" → "Library" → **"YouTube Data API v3"** search karke
   Enable karo.
3. "APIs & Services" → "Credentials" → "Create Credentials" → **"OAuth
   client ID"** → Application type: **Desktop app**.
4. JSON file download karo, uska naam badal ke `client_secret.json` rakho,
   project folder (jahan `config.yaml` hai) mein rakho.
5. "OAuth consent screen" mein apni Google ID ko "Test user" ke taur par
   add karo (jab tak app verify nahi karwate, sirf test users hi login kar
   paayenge — tumhara hi channel hai to ye kaafi hai).

Ab ek-baar ka login karo:
```bash
python src/upload_youtube.py --auth
```
Browser khulega, apne YouTube wale Google account se login/allow karo. Ek
`token.json` file ban jaayegi — iska pura content copy kar lo, aage
GitHub Secret mein daalna hai.

### Step 2: Facebook Page + access token banao

1. Facebook par ek **Page** banao (personal profile nahi — automation sirf
   Page par chalta hai).
2. [Meta for Developers](https://developers.facebook.com/) par jaake ek app
   banao (type: "Business").
3. Graph API Explorer (developers.facebook.com/tools/explorer) use karke
   apni Page ke liye ek access token generate karo, permissions mein
   `pages_manage_posts` aur `pages_read_engagement` select karo.
4. Us short-lived token ko long-lived Page token mein convert karo (Meta ke
   docs mein "long-lived page access token" step hai — ek simple API call
   hai, doc mein exact steps hain).
5. Apni Page ka **numeric Page ID** bhi note kar lo (Page → About mein milta
   hai, ya Graph API Explorer se).

### Step 3: (Optional) Behtar narration ke liye free Gemini key

[Google AI Studio](https://aistudio.google.com/) par jaake free API key le
lo (koi credit card nahi chahiye). `config.yaml` mein `script_mode: "ai"`
kar do.

### Step 4: GitHub par daalo aur secrets add karo

1. Naya **GitHub repository** banao (private rakh sakte ho), is poore
   folder ko push karo.
2. Repo → **Settings → Secrets and variables → Actions → New repository
   secret** — ye secrets add karo:

   | Secret name | Value |
   |---|---|
   | `YOUTUBE_TOKEN_JSON` | Step 1 wali `token.json` ka pura content |
   | `FB_PAGE_ID` | Step 2 wali Page ID |
   | `FB_PAGE_ACCESS_TOKEN` | Step 2 wala long-lived token |
   | `GEMINI_API_KEY` | (optional) Step 3 wali key |

3. Repo ke **"Actions"** tab mein jaao, workflow ko enable karo. Bas — ab ye
   roz apne aap chalega (`.github/workflows/daily-news-bot.yml` mein time
   set hai, chaho to badal do).

### Ek-baar manually test karo (recommended, GitHub push karne se pehle)

```bash
python src/main.py
```
Pehli baar `config.yaml` mein `privacy_status: "unlisted"` rakho, taaki
public jaane se pehle video check kar sako.

---

## Customize karna

Sab `config.yaml` se hota hai — code chhedna nahi padta:
- `top_n` — kitni news (10 / 50 / 100)
- `rss_feeds` — apni pasand ke news source add/remove karo
- `voice` — Hindi/English/koi bhi edge-tts voice
- `video.make_shorts` — Shorts video on/off
- `publish.youtube / youtube_shorts / facebook` — kahan-kahan post karna hai

---

## Troubleshooting

- **Hindi text boxes/blank dikh raha hai** → font missing, `assets/fonts/`
  wali note file dekho.
- **YouTube upload fails: quotaExceeded** → free daily quota khatam,
  agle din reset hoga, ya `top_n` kam karo.
- **Facebook upload fails: permission denied** → token expire ho gaya (long-
  lived bhi ~60 din mein expire hota hai) — naya token generate karo.
- **GitHub Actions run fail ho raha hai** → Actions tab → us run ko kholo →
  logs padho, ya "run-output" artifact download karke video/log dekho.

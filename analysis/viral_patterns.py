from __future__ import annotations

import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path


DATA_PATH = Path("data/viral_samples.csv")
OUT_DIR = Path("outputs/patterns")
OUT_DIR.mkdir(parents=True, exist_ok=True)

STOPWORDS = {
    "dan", "yang", "di", "ke", "dari", "the", "to", "of", "a", "an", "in",
    "ini", "itu", "akan", "jadi", "untuk", "dengan", "on", "by", "for",
    "video", "photo", "tiktok", "rt", "sudah", "lagi", "banget",
}

THEME_KEYWORDS = {
    "announcement": ["umumkan", "siap rilis", "rilis", "announce", "released"],
    "achievement": ["resmi", "pengisi", "anthem", "world championship", "tampil", "perdana"],
    "global": ["amerika", "dunia", "global", "international", "world"],
    "reaction": ["reaction", "reacts", "reactions", "reaksi"],
    "dance": ["ngedance", "dance", "dancer", "choreo", "gerak"],
    "song": ["lagu", "track", "soundtrack", "single"],
    "profile": ["profil", "member"],
}


def parse_views(text: str) -> int:
    t = text.strip().lower().replace(" ", "")
    t = t.replace(",", ".")
    m = re.match(r"(\d+(?:\.\d+)?)", t)
    if not m:
        return 0
    num = float(m.group(1))
    if "jt" in t or "juta" in t or "m" in t:
        return int(num * 1_000_000)
    if "rb" in t or "k" in t:
        return int(num * 1_000)
    return int(num)


def tokenize(text: str) -> list[str]:
    t = re.sub(r"https?://\S+", "", text.lower())
    t = re.sub(r"[^a-z0-9\s]+", " ", t)
    words = [w for w in t.split() if w and w not in STOPWORDS]
    return words


def detect_themes(text: str) -> list[str]:
    t = text.lower()
    found = []
    for theme, kws in THEME_KEYWORDS.items():
        if any(k in t for k in kws):
            found.append(theme)
    return found or ["general"]


def main():
    rows = []
    # Try utf-8 first, fallback to cp1252/latin-1 for messy CSVs
    encodings = ["utf-8", "cp1252", "latin-1"]
    f = None
    for enc in encodings:
        try:
            f = DATA_PATH.open("r", encoding=enc)
            header = f.readline()
            f.seek(0)
            delimiter = ";" if ";" in header else ","
            reader = csv.DictReader(f, delimiter=delimiter)
            break
        except UnicodeDecodeError:
            if f:
                f.close()
            f = None
            continue
    if f is None:
        raise RuntimeError("Failed to decode CSV with utf-8/cp1252/latin-1")
    with f:
        for r in reader:
            views = r.get("views") or ""
            views_num = int(views) if views else parse_views(r.get("views_text", ""))
            rows.append({
                "platform": r.get("platform", "").strip(),
                "text": (r.get("text") or r.get("caption") or "").strip(),
                "url": r.get("url", "").strip(),
                "views_text": r.get("views_text", "").strip(),
                "views": views_num,
                "likes": int((r.get("Likes") or "0").replace(",", "") or 0),
                "comments": int((r.get("Comments") or "0").replace(",", "") or 0),
                "shares": int((r.get("Shares") or "0").replace(",", "") or 0),
                "hashtags": (r.get("Hashtag") or "").strip(),
            })

    token_counts = Counter()
    bigram_counts = Counter()
    theme_counts = Counter()
    theme_views = defaultdict(list)

    for r in rows:
        words = tokenize(r["text"])
        token_counts.update(words)
        bigrams = list(zip(words, words[1:]))
        bigram_counts.update([" ".join(b) for b in bigrams])
        themes = detect_themes(r["text"])
        for th in themes:
            theme_counts[th] += 1
            theme_views[th].append(r["views"])

    engagement = []
    for r in rows:
        if r["views"] > 0:
            eng = (r["likes"] + r["comments"] + r["shares"]) / r["views"]
            engagement.append(eng)
    avg_engagement = float(sum(engagement) / max(1, len(engagement)))

    top_words = token_counts.most_common(20)
    top_bigrams = bigram_counts.most_common(15)

    theme_summary = []
    for th, cnt in theme_counts.items():
        v = theme_views.get(th) or [0]
        theme_summary.append({
            "theme": th,
            "count": cnt,
            "avg_views": int(sum(v) / max(1, len(v))),
            "max_views": max(v),
        })
    theme_summary = sorted(theme_summary, key=lambda x: x["avg_views"], reverse=True)

    report = {
        "rows": len(rows),
        "top_words": top_words,
        "top_bigrams": top_bigrams,
        "themes": theme_summary,
        "avg_engagement_rate": round(avg_engagement, 6),
    }

    (OUT_DIR / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    inspirations = [
        "Buka dengan hook singkat + nama artis/lagu, lanjut konteks penting (event/rilis).",
        "Highlight momen spesifik: bagian dance/pose/line yang bikin candu.",
        "Tekankan capaian global: tampil di event besar, media luar, kolaborasi.",
        "Gunakan kata kerja kuat: diumumkan, resmi, diperkenalkan, debut.",
        "Akhiri dengan CTA ringan/hashtag relevan (tanpa harus selalu sama).",
    ]
    note = "Catatan: ini inspirasi, bukan template wajib. Pakai fleksibel sesuai konten."
    (OUT_DIR / "templates.txt").write_text(note + "\n\n" + "\n".join(inspirations), encoding="utf-8")

    feature_keywords = {
        "announcement": THEME_KEYWORDS["announcement"],
        "achievement": THEME_KEYWORDS["achievement"],
        "global": THEME_KEYWORDS["global"],
        "reaction": THEME_KEYWORDS["reaction"],
        "dance": THEME_KEYWORDS["dance"],
        "song": THEME_KEYWORDS["song"],
        "profile": THEME_KEYWORDS["profile"],
    }
    (OUT_DIR / "feature_keywords.json").write_text(
        json.dumps(feature_keywords, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print("[OK] report.json, templates.txt, feature_keywords.json written to outputs/patterns/")


if __name__ == "__main__":
    main()

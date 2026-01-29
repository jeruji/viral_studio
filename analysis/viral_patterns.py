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
    with DATA_PATH.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            views = r.get("views") or ""
            views_num = int(views) if views else parse_views(r.get("views_text", ""))
            rows.append({
                "platform": r.get("platform", "").strip(),
                "text": r.get("text", "").strip(),
                "url": r.get("url", "").strip(),
                "views_text": r.get("views_text", "").strip(),
                "views": views_num,
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
    }

    (OUT_DIR / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    templates = [
        "🔥 {artist} diumumkan tampil di {event} — siap live pertama kalinya!",
        "Makin mendunia! {artist} diperkenalkan di {media} luar negeri.",
        "Candu banget lihat {member} di bagian ini 😍",
        "{song} resmi jadi soundtrack {franchise} — hype maksimal.",
        "Reaksi pertama kali dengar {song}: {reaction}",
    ]
    (OUT_DIR / "templates.txt").write_text("\n".join(templates), encoding="utf-8")

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

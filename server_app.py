import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
import json
import requests

app = FastAPI()

# ---- Static refs ----
REF_DIR = os.getenv("REF_DIR", "outputs/ref")
Path(REF_DIR).mkdir(parents=True, exist_ok=True)

# static files will be available at /ref/<filename>
app.mount("/ref", StaticFiles(directory=REF_DIR), name="ref")


# ---- Kie callback ----
OUT_DIR = Path(os.getenv("OUTPUT_DIR", "outputs")) / "kie"
OUT_DIR.mkdir(parents=True, exist_ok=True)

@app.post("/kie/callback")
async def kie_callback(req: Request):
    payload = await req.json()

    (OUT_DIR / "last_callback.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    data = payload.get("data") or {}
    info = data.get("info") or {}

    task_id = (
        payload.get("taskId")
        or payload.get("task_id")
        or data.get("taskId")
        or data.get("task_id")
        or info.get("taskId")
        or info.get("task_id")
        or "result"
    )

    video_url = (
        payload.get("videoUrl")
        or payload.get("video_url")
        or data.get("videoUrl")
        or data.get("video_url")
        or info.get("videoUrl")
        or info.get("video_url")
    )

    if not video_url:
        urls = info.get("resultUrls") or info.get("result_urls") or []
        if isinstance(urls, list) and urls:
            video_url = urls[0]

    if not video_url:
        return {
            "ok": True,
            "msg": "callback received but no video URL found",
            "taskId": task_id,
            "keys": list(payload.keys()),
        }

    out_path = OUT_DIR / f"{task_id}.mp4"
    r = requests.get(video_url, timeout=300)
    r.raise_for_status()
    out_path.write_bytes(r.content)

    print("[KIE] Video downloaded:", out_path)
    return {"ok": True, "saved": str(out_path), "taskId": task_id}


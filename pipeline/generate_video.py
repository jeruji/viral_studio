from __future__ import annotations
from pathlib import Path
import os
import time
import uuid
import json

def _wait_for_file(path: str, timeout_sec: int = 600, min_bytes: int = 200_000) -> bool:
    p = Path(path)
    t0 = time.time()
    while time.time() - t0 < timeout_sec:
        if p.exists():
            try:
                if p.stat().st_size >= min_bytes:
                    return True
            except OSError:
                pass
        time.sleep(2)
    return False


def generate_videos_kie(kie_client, video_prompts, profile, platform_name: str, image_urls: list[str], callback_url: str | None):
    out_dir = Path(os.getenv("OUTPUT_DIR", "outputs"))
    out_dir.mkdir(parents=True, exist_ok=True)

    # NOTE: platform aspect for planning only; Kie may override for reference mode
    aspect = profile.get("ratio", "9:16")
    aspect_ratio = "9:16" if aspect == "9:16" else "16:9"

    videos = []
    for i, sp in enumerate(video_prompts, start=1):
        variant = sp.get("variant", f"V{i}")
        prompt = sp["prompt"]
        variant_root = sp.get("variant_root", variant)
        segment_index = sp.get("segment_index")
        segment_total = sp.get("segment_total")

        planned_out = out_dir / f"{platform_name}_{i:02d}_{variant}.mp4"

        data = kie_client.generate_reference2video(
            prompt=prompt,
            image_urls=image_urls,
            aspect_ratio=aspect_ratio,
            callback_url=callback_url,
            out_path=str(planned_out),
            seeds=None,
        )

        # IMPORTANT: actual file will be downloaded by callback server to outputs/kie/<taskId>.mp4
        task_id = data.get("taskId") if isinstance(data, dict) else None
        downloaded = str(out_dir / "kie" / f"{task_id}.mp4") if task_id else ""
        global_downloaded = str(Path("outputs") / "kie" / f"{task_id}.mp4") if task_id else ""

        # Optional: wait until file exists so downstream (rescore/merge) works immediately
        if downloaded:
            if not _wait_for_file(downloaded, timeout_sec=600):
                # fallback: callback server might be writing to global outputs/kie
                if global_downloaded and _wait_for_file(global_downloaded, timeout_sec=60):
                    downloaded = global_downloaded

        videos.append(
            {
                "path": str(planned_out),          # planned name
                "final_path": downloaded or "",    # actual downloaded file path
                "variant": variant,
                "variant_root": variant_root,
                "segment_index": segment_index,
                "segment_total": segment_total,
                "prompt": prompt,
                "kie_response": data,
                "taskId": task_id,
            }
        )

    return videos

def generate_videos_kie_simulate(video_prompts, platform_name: str, image_urls=None):
    """
    SIMULATE mode: no API call.
    Produces prompts + taskIds. You will manually place mp4 files at:
      outputs/kie/<taskId>.mp4

    image_urls:
      - in simulate, can be LOCAL PATHS to extracted ref images (outputs/ref/*.jpg)
      - or public URLs, up to you.
    """
    image_urls = image_urls or []

    out_dir = Path(os.getenv("OUTPUT_DIR", "outputs"))
    kie_dir = out_dir / "kie"
    out_dir.mkdir(parents=True, exist_ok=True)
    kie_dir.mkdir(parents=True, exist_ok=True)

    tasks = []
    videos = []

    for i, sp in enumerate(video_prompts, start=1):
        variant = sp.get("variant", f"V{i}")
        prompt = sp["prompt"]
        variant_root = sp.get("variant_root", variant)
        segment_index = sp.get("segment_index")
        segment_total = sp.get("segment_total")

        task_id = f"manual_{platform_name}_{i:02d}_{uuid.uuid4().hex[:10]}"

        planned_out = out_dir / f"{platform_name}_{i:02d}_{variant}.mp4"
        final_path = kie_dir / f"{task_id}.mp4"

        tasks.append({
            "platform": platform_name,
            "i": i,
            "variant": variant,
            "variant_root": variant_root,
            "segment_index": segment_index,
            "segment_total": segment_total,
            "taskId": task_id,
            "prompt": prompt,
            "reference_images": list(image_urls),
            "instruction": "Use the same character/person as in reference_images (if provided). Keep identity consistent.",
            "save_as": str(final_path),
            "planned_out": str(planned_out),
        })

        videos.append({
            "path": str(planned_out),
            "final_path": str(final_path),
            "variant": variant,
            "variant_root": variant_root,
            "segment_index": segment_index,
            "segment_total": segment_total,
            "prompt": prompt,
            "taskId": task_id,
            "ref_images": list(image_urls),
            "kie_response": {"taskId": task_id, "mode": "simulate"},
        })

    tasks_file = kie_dir / "tasks.json"
    # overwrite to keep only latest simulate run
    tasks_file.write_text(json.dumps(tasks, indent=2, ensure_ascii=False), encoding="utf-8")

    return videos

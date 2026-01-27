from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os
import requests


@dataclass
class KieConfig:
    token: str | None = None
    base_url: str = "https://api.kie.ai/api/v1/veo"
    model: str = "veo3_fast"
    enable_translation: bool = True
    enable_fallback: bool = False
    watermark: str | None = None
    force_reference_aspect_ratio: str | None = None


class KieVeoClient:
    def __init__(self, cfg: KieConfig | None = None):
        self.cfg = cfg or KieConfig()
        if self.cfg.token is None:
            self.cfg.token = os.getenv("KIE_TOKEN")

    def generate_reference2video(
        self,
        prompt: str,
        image_urls: list[str],
        aspect_ratio: str,
        callback_url: str | None,
        out_path: str,
        seeds: int | None = None,
    ) -> dict:
        if not self.cfg.token:
            raise RuntimeError("KIE_TOKEN not set")

        # Determine generation type
        gen_type = "REFERENCE_2_VIDEO" if image_urls else "TEXT_2_VIDEO"

        # Follow requested aspect; allow optional override for reference mode.
        if gen_type == "REFERENCE_2_VIDEO" and self.cfg.force_reference_aspect_ratio:
            effective_aspect = self.cfg.force_reference_aspect_ratio
        else:
            effective_aspect = aspect_ratio

        payload = {
            "prompt": prompt,
            "imageUrls": image_urls or [],
            "model": self.cfg.model,
            "watermark": self.cfg.watermark,
            "callBackUrl": callback_url,
            "aspectRatio": effective_aspect,
            "seeds": seeds,
            "enableFallback": self.cfg.enable_fallback,
            "enableTranslation": self.cfg.enable_translation,
            "generationType": gen_type,
        }

        headers = {
            "Authorization": f"Bearer {self.cfg.token}",
            "Content-Type": "application/json"
        }

        r = requests.post(f"{self.cfg.base_url}/generate", json=payload, headers=headers, timeout=120)

        # ---- parse response safely ----
        try:
            data = r.json()
            print("[KIE DEBUG] response:", data)
        except Exception:
            raise RuntimeError(f"Kie returned non-JSON response: status={r.status_code} text={r.text[:500]}")

        # ---- explicit API error handling ----
        code = data.get("code")
        msg = data.get("msg")

        if r.status_code != 200 or code != 200:
            raise RuntimeError(f"Kie API error: http={r.status_code} code={code} msg={msg} full={data}")

        # ---- taskId extraction robust ----
        d = data.get("data")
        task_id = None
        if isinstance(d, dict):
            task_id = d.get("taskId") or d.get("task_id") or d.get("id")
        # Sometimes APIs return taskId at top-level
        task_id = task_id or data.get("taskId") or data.get("task_id")

        if not task_id:
            raise RuntimeError(
                "Kie generate returned success but taskId missing / data is null. "
                f"full_response={data}"
            )

        print(f"[KIE] taskId created: {task_id}")

        return {
            "taskId": task_id,
            "out_path": out_path,
            "raw": data
        }

    def download_video(self, video_url: str, out_path: str) -> str:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        vr = requests.get(video_url, timeout=300)
        vr.raise_for_status()
        Path(out_path).write_bytes(vr.content)
        return out_path

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import time
import subprocess
import requests


@dataclass
class SoraConfig:
    # Set these if you already have a Sora endpoint flow.
    # If empty, we will fallback to placeholder mp4 (so pipeline still works).
    api_base: str | None = None          # e.g. "https://api.openai.com/v1" (example)
    api_key: str | None = None           # from env OPENAI_API_KEY
    model: str = "sora-2"                # or sora-2-pro
    poll_interval_sec: float = 2.0
    timeout_sec: int = 600

    # Optional: if you want to always ensure your original song is merged in final output
    merge_audio: bool = False
    audio_path: str | None = None        # path to mp3/wav to merge (if merge_audio=True)


class SoraClient:
    def __init__(self, config: SoraConfig | None = None):
        self.cfg = config or SoraConfig()
        if self.cfg.api_key is None:
            self.cfg.api_key = os.getenv("OPENAI_API_KEY")

    def generate_video(self, prompt: str, ratio: str, duration: int, out_path: str) -> str:
        """
        Generates a video file at out_path and returns the final path.
        If API config not provided, creates a placeholder mp4 (debug-friendly).
        """
        out_path = str(Path(out_path))
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)

        print("[SORA] Generating video:", prompt[:80])
        print("[SORA] out_path:", out_path)

        # If you haven't wired Sora API yet, we still create a placeholder file.
        if not self.cfg.api_base or not self.cfg.api_key:
            print("[SORA] WARNING: Sora API not configured. Writing placeholder mp4.")
            self._write_placeholder_mp4(out_path, text="PLACEHOLDER SORA OUTPUT")
            # merge audio if requested
            if self.cfg.merge_audio and self.cfg.audio_path:
                out_path = self._merge_audio(out_path, self.cfg.audio_path)
            return out_path

        # ====== REAL SORA FLOW (template) ======
        # You MUST adapt endpoints/payload to your Sora API interface.
        # The important part: we do (create job) -> (poll) -> (download video bytes/url) -> write mp4

        job = self._create_sora_job(prompt=prompt, ratio=ratio, duration=duration)
        video_bytes = self._poll_and_download(job)

        Path(out_path).write_bytes(video_bytes)

        if self.cfg.merge_audio and self.cfg.audio_path:
            out_path = self._merge_audio(out_path, self.cfg.audio_path)

        return out_path

    # -------------------------
    # TEMPLATE: Sora API calls
    # -------------------------
    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.cfg.api_key}",
            "Content-Type": "application/json",
        }

    def _create_sora_job(self, prompt: str, ratio: str, duration: int) -> dict:
        """
        Template. Replace endpoint + payload to match Sora API you use.
        Expected return: dict containing job id / status url / etc.
        """
        url = f"{self.cfg.api_base}/sora/generations"  # <-- placeholder endpoint
        payload = {
            "model": self.cfg.model,
            "prompt": prompt,
            "duration": duration,
            "aspect_ratio": ratio,
        }
        r = requests.post(url, headers=self._headers(), json=payload, timeout=60)
        r.raise_for_status()
        return r.json()

    def _poll_and_download(self, job: dict) -> bytes:
        """
        Template. Replace with your real fields:
          - job_id
          - status polling endpoint
          - download url field
        """
        job_id = job.get("id") or job.get("job_id")
        if not job_id:
            raise RuntimeError(f"Sora job missing id fields: {job}")

        status_url = job.get("status_url") or f"{self.cfg.api_base}/sora/generations/{job_id}"
        deadline = time.time() + self.cfg.timeout_sec

        while time.time() < deadline:
            r = requests.get(status_url, headers=self._headers(), timeout=60)
            r.raise_for_status()
            data = r.json()
            status = (data.get("status") or "").lower()

            if status in ("succeeded", "completed", "success"):
                # Could be a direct url or base64; we assume URL here
                video_url = (
                    data.get("video_url")
                    or data.get("output_url")
                    or (data.get("output", {}) or {}).get("url")
                )
                if not video_url:
                    raise RuntimeError(f"Sora succeeded but no video url in response: {data}")

                vr = requests.get(video_url, timeout=120)
                vr.raise_for_status()
                return vr.content

            if status in ("failed", "error", "canceled", "cancelled"):
                raise RuntimeError(f"Sora generation failed: {data}")

            time.sleep(self.cfg.poll_interval_sec)

        raise TimeoutError("Sora generation timed out")

    # -------------------------
    # Utilities: placeholder + audio merge
    # -------------------------
    def _write_placeholder_mp4(self, out_path: str, text: str = "PLACEHOLDER"):
        """
        Writes a tiny mp4 placeholder using ffmpeg if available,
        otherwise writes an empty file (still creates a path).
        """
        # Try ffmpeg (preferred)
        if self._has_ffmpeg():
            # 3 seconds black video with text would require drawtext; keep simple black
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "color=c=black:s=720x1280:d=3",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                out_path
            ]
            subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if Path(out_path).exists() and Path(out_path).stat().st_size > 0:
                return

        # Fallback: create empty file to satisfy pipeline
        Path(out_path).write_bytes(b"")

    def _merge_audio(self, video_path: str, audio_path: str) -> str:
        """
        Merges provided audio into the video via ffmpeg.
        Output: <original>_with_audio.mp4
        """
        if not self._has_ffmpeg():
            print("[SORA] WARNING: ffmpeg not found; cannot merge audio.")
            return video_path

        video_path = str(Path(video_path))
        audio_path = str(Path(audio_path))

        out_path = str(Path(video_path).with_name(Path(video_path).stem + "_with_audio.mp4"))

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            out_path
        ]
        subprocess.run(cmd, check=True)
        return out_path

    def _has_ffmpeg(self) -> bool:
        try:
            subprocess.run(["ffmpeg", "-version"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            return False

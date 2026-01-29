# main.py
import argparse
import json
from pathlib import Path
import os
import re
import math

from ml.feature_audio import extract_audio_features
from ml.feature_text import extract_text_features
from ml.feature_video import extract_video_features
from ml.scorer import ViralityScorer

from llm.gpt52_client import GPT52Client
from pipeline.build_brief import build_creative_brief
from pipeline.generate_creative import generate_creative

from ml.character_crop import extract_person_refs
from video_gen.kie_client import KieVeoClient, KieConfig

from pipeline.generate_video import generate_videos_kie
from pipeline.rescore_select import select_best
from audio_remix.remix_engine import AudioRemixEngine
from audio_remix.presets import (
    preset_jedag_jedug,
    preset_tiktok_house,
    preset_mellow_rainy,
    preset_cinematic_epic,
    preset_lofi_chill,
)
import subprocess
from pipeline.generate_video import generate_videos_kie_simulate
import cv2

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "outputs"))

def parse_args():
    p = argparse.ArgumentParser(
        description="Viral Studio: Multi-platform creative + Video + ML re-scoring"
    )

    p.add_argument("--audio", required=False, help="Path to audio file (mp3/wav)")
    p.add_argument("--lyrics", required=False, help="Path to lyrics txt (optional)")
    p.add_argument("--description", default="", help="Optional description (used when lyrics not provided)")
    p.add_argument("--content-type", choices=["music", "general"], default="music",
                   help="Content type: music uses audio+lyrics; general can be caption-only")
    p.add_argument("--mood", required=True, choices=["happy", "hype", "sad", "mellow", "nostalgic"])
    p.add_argument("--remix", action="store_true", help="Enable audio adaptation/remix for each platform")
        # --- Character reference extraction (from source video) ---
    p.add_argument("--use-character-ref", action="store_true", help="Extract person/face crops from --video for reference-to-video")
    p.add_argument("--ref-frames", type=int, default=6, help="How many reference images to extract from video")
    p.add_argument("--ref-frame-stride", type=int, default=15, help="Sample every N frames when extracting refs")

    # --- Kie.ai Veo settings ---
    p.add_argument("--kie-token", default=None, help="Kie.ai API token (optional; fallback to env KIE_TOKEN)")
    p.add_argument("--ref-base-url", default=None, help="Public base URL for reference images, e.g. https://xxxx.ngrok-free.dev/ref")
    p.add_argument("--kie-callback-url", default=None, help="Public callback URL for Kie, e.g. https://xxxx.ngrok-free.dev/kie/callback")


    p.add_argument(
        "--audio-style",
        choices=["jedag_jedug", "tiktok_house", "mellow_rainy", "cinematic_epic", "lofi_chill"],
        default=None,
        help="Force audio remix style (optional)"
    )
    p.add_argument(
        "--drum-loop",
        default=None,
        help="Optional path to legal drum loop wav"
    )

    p.add_argument(
        "--caption",
        default="",
        help="Optional seed caption (will influence text features + LLM)"
    )

    p.add_argument(
        "--video",
        default=None,
        help="Optional source video/footage path (if provided, OpenCV features will be extracted)"
    )
    p.add_argument("--skip-video-gen", action="store_true",
               help="Skip video generation; only produce captions/hashtags")

    p.add_argument(
        "--platforms",
        nargs="+",
        default=["tiktok", "instagram", "youtube_short", "youtube_video"],
        help="Platforms to generate for (default: all)"
    )

    p.add_argument(
        "--profiles",
        default="config/platform_profiles.json",
        help="Path to platform_profiles.json"
    )

    p.add_argument(
        "--openai-key",
        default=None,
        help="OpenAI API key (optional; will fallback to env OPENAI_API_KEY)"
    )

    p.add_argument(
        "--variants-per-platform",
        type=int,
        default=3,
        help="How many Video prompt variants to generate per platform (LLM should output at least this many)"
    )

    p.add_argument(
        "--clip-seg-sec",
        type=float,
        default=None,
        help="Split each prompt into N segments of this many seconds, then concat per prompt"
    )

    p.add_argument("--simulate-video", action="store_true",
               help="Do not call Kie API. Only output prompts + taskIds; you will place mp4 manually in outputs/kie/<taskId>.mp4")
    
    p.add_argument("--resume-from-kie", action="store_true",
               help="Skip generation and use existing outputs/kie/tasks.json + mp4 files for scoring/merge")


    return p.parse_args()


def load_profiles(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _coerce_video_path(video_obj):
    # video_obj can be dict (selected item) or string path
    if isinstance(video_obj, (str, Path)):
        return str(video_obj)
    if isinstance(video_obj, dict):
        # prefer final_path if present, else path
        p = video_obj.get("final_path") or video_obj.get("path")
        if p:
            return str(p)
        # fallback: try taskId-based callback download path
        kr = video_obj.get("kie_response") or {}
        tid = None
        if isinstance(kr, dict):
            tid = kr.get("taskId") or (kr.get("raw") or {}).get("data", {}).get("taskId")
        if not tid:
            tid = video_obj.get("taskId")
        if tid:
            primary = OUTPUT_DIR / "kie" / f"{tid}.mp4"
            if primary.exists():
                return str(primary)
            # fallback to global outputs (callback server may write here)
            fallback = Path("outputs") / "kie" / f"{tid}.mp4"
            return str(fallback)
    raise TypeError(f"video_obj must be path-like or dict with path/final_path/taskId, got {type(video_obj).__name__}")

def _probe_duration_sec(path: str) -> float | None:
    try:
        p = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", path],
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    if p.returncode != 0:
        return None
    try:
        return float((p.stdout or "").strip())
    except ValueError:
        return None

def _probe_video_params(path: str) -> tuple[int, int, float] | None:
    try:
        p = subprocess.run(
            [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=width,height,r_frame_rate",
                "-of", "default=nw=1:nk=1", path,
            ],
            capture_output=True,
            text=True,
        )
    except Exception:
        return None

def _pick_best_segment_start(video_path: str, target_dur: float, sample_every_n_frames: int = 5) -> float:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return 0.0

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration_sec = frame_count / fps if fps > 0 else 0.0
    if duration_sec <= target_dur or target_dur <= 0:
        cap.release()
        return 0.0

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    sec_bins = int(duration_sec) + 2
    motion = [0.0] * sec_bins
    faces = [0] * sec_bins
    prev_gray = None
    idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        idx += 1
        if idx % sample_every_n_frames != 0:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        t = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
        sec = int(t)
        if prev_gray is not None:
            diff = cv2.absdiff(gray, prev_gray)
            motion[sec] += float(cv2.mean(diff)[0])
        prev_gray = gray
        fs = face_cascade.detectMultiScale(gray, 1.1, 4)
        if len(fs) > 0:
            faces[sec] += 1

    cap.release()

    window = max(1, int(target_dur))
    best_start = 0
    best_score = -1.0
    for s in range(0, max(1, sec_bins - window)):
        mot = sum(motion[s:s + window])
        fac = sum(faces[s:s + window])
        score = mot + (fac * 50.0)
        if score > best_score:
            best_score = score
            best_start = s
    return float(best_start)

def _trim_video_best(video_path: str, target_dur: float, out_path: str) -> str:
    start = _pick_best_segment_start(video_path, target_dur)
    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{start:.2f}",
        "-t", f"{target_dur:.2f}",
        "-i", video_path,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        out_path,
    ]
    print("[FFMPEG]", " ".join(cmd))
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(
            "ffmpeg trim failed\n"
            f"STDOUT:\n{p.stdout}\n\nSTDERR:\n{p.stderr}"
        )
    return out_path
    if p.returncode != 0:
        return None
    try:
        lines = [l.strip() for l in (p.stdout or "").splitlines() if l.strip()]
        w = int(lines[0])
        h = int(lines[1])
        fps_num, fps_den = lines[2].split("/")
        fps = float(fps_num) / float(fps_den)
        return w, h, fps
    except Exception:
        return None

def _concat_videos_fadeblack(video_paths: list[str], out_path: str, transition_sec: float) -> str:
    if len(video_paths) < 2:
        return video_paths[0] if video_paths else ""

    base = _probe_video_params(video_paths[0])
    if not base:
        raise RuntimeError(f"ffprobe failed to read video params for: {video_paths[0]}")
    base_w, base_h, base_fps = base

    durations = []
    for p in video_paths:
        d = _probe_duration_sec(p)
        if d is None:
            raise RuntimeError(f"ffprobe failed to read duration for: {p}")
        durations.append(d)

    # Build xfade chain with fadeblack transition.
    filters = []
    for i in range(len(video_paths)):
        # scale/pad to base size to avoid xfade size mismatch
        filters.append(
            f"[{i}:v]scale={base_w}:{base_h}:force_original_aspect_ratio=decrease,"
            f"pad={base_w}:{base_h}:(ow-iw)/2:(oh-ih)/2:color=black,"
            f"fps={base_fps},setsar=1,setpts=PTS-STARTPTS[v{i}]"
        )

    offset = durations[0]
    last = "v0"
    for i in range(1, len(video_paths)):
        offset = offset - transition_sec
        filters.append(
            f"[{last}][v{i}]xfade=transition=fadeblack:duration={transition_sec:.3f}:offset={offset:.3f}[v{i}x]"
        )
        last = f"v{i}x"
        offset = offset + durations[i]

    filter_complex = ";".join(filters)

    cmd = ["ffmpeg", "-y"]
    for p in video_paths:
        cmd.extend(["-i", p])
    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", f"[{last}]",
        "-an",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        out_path,
    ])

    print("[FFMPEG]", " ".join(cmd))
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(
            "ffmpeg concat failed\n"
            f"STDOUT:\n{p.stdout}\n\nSTDERR:\n{p.stderr}"
        )

    if not os.path.exists(out_path) or os.path.getsize(out_path) < 100_000:
        raise RuntimeError(f"ffmpeg concat reported success but output missing/too small: {out_path}")

    return out_path

def _collect_concat_paths(candidates: list[str], target_dur: float, transition_sec: float) -> list[str]:
    ordered_paths = []
    total = 0.0
    for p in candidates:
        if p and os.path.exists(p):
            d = _probe_duration_sec(p)
            if d is None:
                continue
            ordered_paths.append(p)
            if len(ordered_paths) == 1:
                total += d
            else:
                total += max(0.0, d - transition_sec)
        if total >= target_dur:
            break
    return ordered_paths

def _storyboard_text(storyboard, audio_style: str | None = None) -> str:
    if not storyboard:
        return ""
    lines = []
    def _normalize_style(text: str) -> str:
        if not audio_style or audio_style == "jedag_jedug":
            return text
        if "jedag" in text.lower():
            for token in ("jedag jedug", "jedag-jedug", "jedag_jedug"):
                text = re.sub(token, audio_style, text, flags=re.IGNORECASE)
        return text
    for beat in storyboard:
        if isinstance(beat, dict):
            t = str(beat.get("t") or "").strip()
            visual = _normalize_style(str(beat.get("visual") or "").strip())
            if not t and not visual:
                continue
            lines.append(f"{t} {visual}".strip())
        elif isinstance(beat, str):
            s = _normalize_style(beat.strip())
            if s:
                lines.append(s)
    if not lines:
        return ""
    return "Storyboard beats:\n- " + "\n- ".join(lines)

def _augment_video_prompts(video_prompts, storyboard, ref_image_urls=None, audio_style: str | None = None) -> list:
    ref_image_urls = ref_image_urls or []
    motion = (
        "Motion directive: full-body choreography and clear subject movement, "
        "multiple shots with noticeable camera motion, not a still-image animation."
    )
    safety = (
        "Safety directive: keep the visuals clean, respectful, and appropriate for all audiences. "
        "No sexualized styling, harmful themes, or risky props; maintain a tasteful, non-violent presentation."
    )
    style_hint = ""
    if audio_style:
        style_hint = f"Music/style directive: match the {audio_style} vibe and pacing."
    character = ""
    if ref_image_urls:
        character = (
            "Character directive: use the provided reference character as the main subject, "
            "keep identity consistent (face, hair, outfit style)."
        )
    def _normalize_style(prompt: str) -> str:
        if not audio_style or audio_style == "jedag_jedug":
            return prompt
        if "jedag" in prompt.lower():
            for token in ("jedag jedug", "jedag-jedug", "jedag_jedug"):
                prompt = re.sub(token, audio_style, prompt, flags=re.IGNORECASE)
        return prompt
    augmented = []
    for vp in video_prompts:
        if not isinstance(vp, dict):
            augmented.append(vp)
            continue
        sb_text = _storyboard_text(vp.get("storyboard") or storyboard, audio_style=audio_style)
        prompt = _normalize_style(str(vp.get("prompt") or "").strip())
        parts = [prompt]
        if sb_text:
            parts.append(sb_text)
        if style_hint:
            parts.append(style_hint)
        if character:
            parts.append(character)
        parts.append(motion)
        parts.append(safety)
        prompt = "\n\n".join(parts)
        vp2 = dict(vp)
        vp2["prompt"] = prompt
        augmented.append(vp2)
    return augmented

def _parse_time_range(t: str) -> tuple[float, float] | None:
    nums = re.findall(r"\d+(?:\.\d+)?", t or "")
    if len(nums) >= 2:
        return float(nums[0]), float(nums[1])
    return None

def _segment_storyboard(storyboard, clip_seg_sec: float, total_dur: float) -> list[list[dict]]:
    if clip_seg_sec <= 0:
        return []
    seg_count = max(1, int(math.ceil(total_dur / clip_seg_sec)))
    segments = [[] for _ in range(seg_count)]
    if not storyboard:
        return segments
    for beat in storyboard:
        if not isinstance(beat, dict):
            continue
        tr = _parse_time_range(str(beat.get("t") or ""))
        if not tr:
            segments[0].append(beat)
            continue
        start, _end = tr
        idx = int(start // clip_seg_sec)
        if 0 <= idx < seg_count:
            segments[idx].append(beat)
    return segments

def _expand_video_prompts_by_segments(video_prompts, storyboard, clip_seg_sec: float, total_dur: float) -> list:
    segments = _segment_storyboard(storyboard, clip_seg_sec, total_dur)
    if not segments:
        return video_prompts
    seg_total = len(segments)
    expanded = []
    def _force_prompt_duration(prompt: str) -> str:
        # Replace explicit duration in prompt with segment duration (e.g., "18–20 seconds" -> "5 seconds")
        prompt = re.sub(
            r"\b\d+(?:\.\d+)?\s*[-–]\s*\d+(?:\.\d+)?\s*(seconds|second|secs|sec|s)\b",
            f"{clip_seg_sec:.0f} seconds",
            prompt,
            count=1,
            flags=re.IGNORECASE,
        )
        return re.sub(
            r"\b\d+(?:\.\d+)?\s*(seconds|second|secs|sec|s)\b",
            f"{clip_seg_sec:.0f} seconds",
            prompt,
            count=1,
            flags=re.IGNORECASE,
        )
    for vp in video_prompts:
        if not isinstance(vp, dict):
            continue
        base_variant = vp.get("variant") or "V1"
        base_prompt = _force_prompt_duration(str(vp.get("prompt") or "").strip())
        for i, seg in enumerate(segments, start=1):
            seg_prompt = (
                f"{base_prompt}\n\nSegment {i}/{seg_total}. "
                f"Clip duration: {clip_seg_sec:.1f}s."
            )
            expanded.append({
                "variant": f"{base_variant}_S{i:02d}",
                "variant_root": base_variant,
                "segment_index": i,
                "segment_total": seg_total,
                "segment_duration": clip_seg_sec,
                "prompt": seg_prompt,
                "storyboard": seg,
            })
    return expanded

def _safe_name(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", s).strip("_")

def _concat_segment_groups(videos: list[dict], out_dir: Path, transition_sec: float) -> list[dict]:
    grouped = {}
    for v in videos:
        if not isinstance(v, dict):
            continue
        root = v.get("variant_root") or v.get("variant") or "V1"
        grouped.setdefault(root, []).append(v)
    concat_videos = []
    for root, items in grouped.items():
        items = sorted(items, key=lambda x: int(x.get("segment_index") or 0))
        paths = []
        for it in items:
            p = _coerce_video_path(it)
            if p and os.path.exists(p):
                paths.append(p)
        if not paths:
            continue
        if len(paths) == 1:
            concat_videos.append({
                "path": paths[0],
                "variant": root,
                "variant_root": root,
                "prompt": items[0].get("prompt", ""),
            })
            continue
        out_path = out_dir / f"{_safe_name(root)}_concat.mp4"
        concat_path = _concat_videos_fadeblack(paths, str(out_path), transition_sec)
        concat_videos.append({
            "path": concat_path,
            "variant": root,
            "variant_root": root,
            "prompt": items[0].get("prompt", ""),
        })
    return concat_videos

def merge_video_audio(video_obj, audio_path: str) -> str:
    # video_obj bisa dict atau str (hasil select_best)
    if video_obj is None:
        raise FileNotFoundError("Video input for merge not found: None")

    video_path = _coerce_video_path(video_obj)
    if not video_path or not os.path.exists(video_path):
        raise FileNotFoundError(f"Video input for merge not found: {video_path}")

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio input for merge not found: {audio_path}")

    out = str(Path(video_path).with_name(Path(video_path).stem + "_final.mp4"))
    Path(out).parent.mkdir(parents=True, exist_ok=True)

    # IMPORTANT: pakai ffmpeg yang ada di PATH
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-map", "0:v:0",     # video dari Kie
        "-map", "1:a:0",     # audio dari lagu kamu
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        out
    ]

    print("[FFMPEG]", " ".join(cmd))
    p = subprocess.run(cmd, capture_output=True, text=True)

    if p.returncode != 0:
        raise RuntimeError(
            "ffmpeg failed\n"
            f"STDOUT:\n{p.stdout}\n\nSTDERR:\n{p.stderr}"
        )

    if not os.path.exists(out) or os.path.getsize(out) < 100_000:
        raise RuntimeError(f"ffmpeg reported success but output missing/too small: {out}")

    return out


def main():
    args = parse_args()

    audio_path = Path(args.audio) if args.audio else None
    lyrics_path = Path(args.lyrics) if args.lyrics else None
    video_path = Path(args.video) if args.video else None

    if args.content_type == "music":
        if not audio_path or not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
    if lyrics_path and not lyrics_path.exists():
        raise FileNotFoundError(f"Lyrics file not found: {lyrics_path}")
    if video_path and not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    lyrics = lyrics_path.read_text(encoding="utf-8", errors="ignore") if lyrics_path else ""
    description = (args.description or "").strip()
    if not lyrics and not description:
        raise ValueError("Provide --lyrics or --description")
    mood = args.mood.lower()
    caption_seed = (args.caption or "").strip()

    # Load platform profiles
    profiles = load_profiles(args.profiles)

    # Filter platforms
    selected = {}
    for p in args.platforms:
        if p in profiles:
            selected[p] = profiles[p]
        else:
            print(f"[WARN] Unknown platform '{p}' (ignored). Valid: {list(profiles.keys())}")

    if not selected:
        raise ValueError("No valid platforms selected.")

    # ====== Feature Extraction ======
    if args.content_type == "music" and audio_path:
        audio_feat = extract_audio_features(str(audio_path))
    else:
        audio_feat = {
            "bpm": 120.0,
            "rms": 0.0,
            "duration_sec": 0.0,
            "spectral_centroid": 0.0,
        }

    # Text features from lyrics + optional caption seed (CTA, sentiment, etc.)
    base_text = lyrics if lyrics else description
    combined_text = (base_text + "\n\n" + caption_seed).strip()
    text_feat = extract_text_features(combined_text)

    # Video features (optional)
    if video_path:
        video_feat = extract_video_features(str(video_path))
    else:
        # default zeros; scorer will also pad missing columns,
        # but this makes it explicit for debugging
        video_feat = {
            "avg_brightness": 0.0,
            "cut_rate_per_min": 0.0,
            "has_faces": 0.0,
            "has_text_overlay": 0.0,
        }

    # Combine features for ML
    base_features = {}
    base_features.update(audio_feat)
    base_features.update(text_feat)
    base_features.update(video_feat)

    # ====== ML prediction (baseline) ======
    scorer = ViralityScorer()
    ml_pred = scorer.predict(base_features)

    # ====== Init LLM + KIE ======
    llm = None
    kie = None
    if not args.resume_from_kie and not args.skip_video_gen:
        llm = GPT52Client(api_key=args.openai_key)
        kie = KieVeoClient(
            KieConfig(token=args.kie_token)
        )


    print("\n===== INPUT SUMMARY =====")
    print("Audio:", str(audio_path) if audio_path else "(none)")
    print("Lyrics:", str(lyrics_path) if lyrics_path else "(none)")
    print("Description:", description if description else "(none)")
    print("Video:", str(video_path) if video_path else "(none)")
    print("Mood:", mood)
    print("Platforms:", list(selected.keys()))
    print("Seed caption:", caption_seed if caption_seed else "(none)")
    print("\n===== BASE FEATURES =====")
    for k in sorted(base_features.keys()):
        print(f"- {k}: {base_features[k]}")
    print("\n===== ML BASELINE =====")
    print("Virality score:", round(ml_pred["virality_score"], 2))
    print("Genre:", ml_pred["genre"], f"({ml_pred.get('genre_label', 'unknown')})")
    print("Audience:", ml_pred["audience"], f"({ml_pred.get('audience_label', 'unknown')})")
    print("=========================\n")

    # ====== Reference image extraction (for KIE / manual simulate) ======
    ref_image_urls = []
    ref_local_paths = []

    if args.use_character_ref:
        if not video_path:
            raise ValueError("--use-character-ref requires --video")

        print("[REF] Extracting character reference images...")

        ref_paths = extract_person_refs(
            str(video_path),
            max_refs=args.ref_frames,
            frame_stride=args.ref_frame_stride
        )

        if not ref_paths:
            raise RuntimeError("No reference images extracted from video.")

        # Always keep local paths (useful for simulate/manual)
        ref_local_paths = [str(Path(p)) for p in ref_paths]

        if args.simulate_video or args.resume_from_kie:
            # No need ngrok/public URLs. Manual generators can upload local images.
            ref_image_urls = ref_local_paths
            print("[REF] (SIMULATE/RESUME) local ref images:")
            for p in ref_image_urls:
                print(" -", p)
        else:
            # Normal KIE API flow needs public URLs
            if not args.ref_base_url:
                raise ValueError("--ref-base-url is required when using --use-character-ref (non-simulate mode)")
            base = args.ref_base_url.rstrip("/")
            for p in ref_paths:
                fname = Path(p).name
                ref_image_urls.append(f"{base}/{fname}")

            print("[REF] imageUrls:")
            for u in ref_image_urls:
                print(" -", u)



    remixer = AudioRemixEngine()

    # ====== Per-platform generation loop ======
    results = {}

    for platform, profile in selected.items():
        print(f"\n=== {platform.upper()} ===")

        if args.resume_from_kie:
            # Load previous creative output if available
            creative_path = OUTPUT_DIR / f"creative_{platform}.json"
            if creative_path.exists():
                try:
                    creative = json.loads(creative_path.read_text(encoding="utf-8"))
                except Exception:
                    creative = {}
            else:
                creative = {}
        else:
            brief = build_creative_brief(
                platform=platform,
                profile=profile,
                mood=mood,
                ml_pred=ml_pred,
                audio_feat=audio_feat,
                lyrics=(lyrics if lyrics else description)
            )

            # Include caption seed so LLM can refine it (optional)
            brief["caption_seed"] = caption_seed

            creative = generate_creative(llm, brief)

        # Merge sora_prompts into video_prompts for a richer prompt pool
        vp = creative.get("video_prompts") or []
        sp = creative.get("sora_prompts") or []
        if isinstance(vp, dict):
            vp = [vp]
        if isinstance(sp, dict):
            sp = [sp]
        if isinstance(vp, list) and isinstance(sp, list):
            merged = vp + sp
            # normalize to list[dict{variant,prompt}]
            normalized = []
            for i, item in enumerate(merged, start=1):
                if isinstance(item, dict):
                    prompt = item.get("prompt")
                    variant = item.get("variant") or f"V{i}"
                    if prompt:
                        normalized.append({"variant": variant, "prompt": prompt})
                elif isinstance(item, str):
                    normalized.append({"variant": f"V{i}", "prompt": item})
            if normalized:
                creative["video_prompts"] = normalized
                creative.pop("sora_prompts", None)

        # Save raw creative output for debugging
        out_dir = OUTPUT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        (raw_path := out_dir / f"creative_{platform}.json").write_text(
            json.dumps(creative, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        print("[DEBUG] Saved creative JSON to:", raw_path)


        # --- Robust extraction of video prompts ---
        video_prompts = (
            creative.get("video_prompts")
        )

        if isinstance(video_prompts, dict):
            video_prompts = [video_prompts]

        if isinstance(video_prompts, list) and video_prompts and isinstance(video_prompts[0], str):
            video_prompts = [{"variant": f"V{i+1}", "prompt": s} for i, s in enumerate(video_prompts)]

        # If still empty -> fallback prompt
        if not video_prompts:
            print(f"[WARN] LLM did not return video_prompts for platform={platform}. Using fallback.")
            ratio = profile.get("ratio", "9:16")
            dur_hi = profile.get("duration", [15, 20])[1]
            platform_style = platform.replace("_", " ")

            style_hint = f" {args.audio_style} vibe," if args.audio_style else ""
            fallback_prompt = (
                f"{'Vertical' if ratio=='9:16' else 'Horizontal'} {platform_style} video, "
                f"{mood} mood,{style_hint} fast engaging social media pacing, "
                f"kinetic text overlays, clean modern look, no logos, no profanity."
            )
            video_prompts = [{"variant": "fallback", "prompt": fallback_prompt}]


        # Limit variants
        video_prompts = video_prompts[: max(1, args.variants_per_platform)]
        # When segmenting, keep one prompt sequence to avoid mixing variants
        if args.clip_seg_sec:
            video_prompts = video_prompts[:1]

        # Split prompts into segments (per clip duration) if requested
        if args.clip_seg_sec:
            target_dur = int(profile.get("duration", [15, 20])[1])
            # round down to whole segments to avoid an extra short segment
            if args.clip_seg_sec > 0:
                target_dur = int((target_dur // args.clip_seg_sec) * args.clip_seg_sec)
                if target_dur <= 0:
                    target_dur = int(args.clip_seg_sec)
            video_prompts = _expand_video_prompts_by_segments(
                video_prompts,
                creative.get("storyboard"),
                args.clip_seg_sec,
                target_dur,
            )

        # Inject storyboard beats + motion directive into prompts
        video_prompts = _augment_video_prompts(
            video_prompts,
            creative.get("storyboard"),
            ref_image_urls=ref_image_urls,
            audio_style=args.audio_style,
        )

        audio_for_platform = str(audio_path) if audio_path else ""

        if args.remix and audio_path and args.content_type == "music":
            src_bpm = audio_feat.get("bpm", 120.0)
            style = args.audio_style

            # AUTO STYLE kalau user tidak memilih
            if style is None:
                if platform in ("tiktok", "instagram", "youtube_short"):
                    style = "jedag_jedug" if mood in ("hype", "happy") else "mellow_rainy"
                else:
                    style = "cinematic_epic"

            if style == "jedag_jedug":
                plan = preset_jedag_jedug(src_bpm, args.drum_loop)
            elif style == "tiktok_house":
                plan = preset_tiktok_house(src_bpm, args.drum_loop)
            elif style == "mellow_rainy":
                plan = preset_mellow_rainy()
            elif style == "cinematic_epic":
                plan = preset_cinematic_epic()
            elif style == "lofi_chill":
                plan = preset_lofi_chill()
            else:
                plan = preset_mellow_rainy()

            target_dur = int(profile.get("duration", [15, 20])[1])
            audio_for_platform, audio_dbg = remixer.apply(
                str(audio_path),
                plan,
                target_duration_sec=target_dur
            )

            print(f"[AUDIO] style={style} -> {audio_for_platform}")

        # generate_videos_kie tetap import kalau mode normal
        if args.skip_video_gen:
            captions = creative.get("captions", [])
            caption_final = captions[0]["text"] if captions else caption_seed or description
            best_vid = str(video_path) if video_path else None
            if video_path:
                target_dur = int(profile.get("duration", [15, 20])[1])
                dur = _probe_duration_sec(str(video_path)) or 0.0
                if dur > target_dur:
                    out_dir = OUTPUT_DIR / "trimmed"
                    out_dir.mkdir(parents=True, exist_ok=True)
                    out_path = out_dir / f"{platform}_best.mp4"
                    best_vid = _trim_video_best(str(video_path), float(target_dur), str(out_path))
            results[platform] = {
                "best_video": best_vid,
                "best_score": None,
                "caption": caption_final,
                "creative": creative,
            }
            continue
        if args.resume_from_kie:
            # load tasks.json and build videos list

            tasks_file = OUTPUT_DIR / "kie" / "tasks.json"
            if not tasks_file.exists():
                raise FileNotFoundError(f"tasks.json not found: {tasks_file}")

            tasks = json.loads(tasks_file.read_text(encoding="utf-8"))
            # filter by platform yang sedang diproses
            tasks_p = [t for t in tasks if t.get("platform") == platform]

            videos = []
            for t in tasks_p:
                videos.append({
                    "path": t.get("planned_out", ""),
                    "final_path": t.get("save_as", ""),
                    "variant": t.get("variant", ""),
                    "variant_root": t.get("variant_root", ""),
                    "segment_index": t.get("segment_index"),
                    "segment_total": t.get("segment_total"),
                    "prompt": t.get("prompt", ""),
                    "taskId": t.get("taskId", ""),
                    "kie_response": {"taskId": t.get("taskId", ""), "mode": "resume"},
                })
        else:
            if args.simulate_video:
                try:
                    videos = generate_videos_kie_simulate(
                        video_prompts,
                        platform_name=platform,
                        image_urls=ref_image_urls,   # <-- penting untuk manual
                    )
                except TypeError:
                    # backward compatible if your simulate function doesn't accept image_urls yet
                    videos = generate_videos_kie_simulate(video_prompts, platform_name=platform)

                print("[SIMULATE] Prompts saved. Generate videos manually and place them as outputs/kie/<taskId>.mp4")
                print("[SIMULATE] Then rerun with --resume-from-kie")

                # In simulate mode we don't have mp4 files yet, so skip scoring/merge.
                results[platform] = {
                    "best_video": None,
                    "best_score": None,
                    "caption": caption_seed,
                    "creative": creative,
                }
                continue

            else:
                videos = generate_videos_kie(
                    kie_client=kie,
                    video_prompts=video_prompts,   # or sora_prompts depending on your signature
                    profile=profile,
                    platform_name=platform,
                    image_urls=ref_image_urls,
                    callback_url=args.kie_callback_url,
                )

        # Concatenate all segments in order when segmentation is enabled
        if args.clip_seg_sec:
            transition_sec = 0.4
            out_dir = OUTPUT_DIR / "kie"
            ordered = []
            # Prefer explicit segment ordering if present (resume mode)
            for v in sorted(videos, key=lambda x: int(x.get("segment_index") or 0)):
                p = _coerce_video_path(v)
                if p and os.path.exists(p):
                    ordered.append(p)
            if len(ordered) >= 2:
                all_out = str(out_dir / f"{platform}_all_concat.mp4")
                all_path = _concat_videos_fadeblack(ordered, all_out, transition_sec)
                print(f"[CONCAT] {platform}: merged {len(ordered)} segments -> {all_path}")
                videos = [{
                    "path": all_path,
                    "variant": "all_concat",
                    "prompt": "Concatenated all segments",
                }]

    base_features["_target_text"] = (f"{platform}\n{args.mood}\n{caption_seed or ''}\n{args.audio_style or ''}\n{(lyrics or description)[:2000]}")

        # Re-score generated videos and pick best
        best_video, best_score = select_best(videos, scorer, base_features)

        if not best_video:
            if args.simulate_video and not args.resume_from_kie:
                raise RuntimeError(
                    f"No generated video files found for platform={platform}. "
                    "You are in --simulate-video mode. Place mp4 files at outputs/kie/<taskId>.mp4 "
                    "and rerun with --resume-from-kie."
                )
            raise RuntimeError(
                    f"No generated video files found for platform={platform}. "
                    f"Check {OUTPUT_DIR / 'kie'} and tasks.json paths."
            )

        best_video_path = _coerce_video_path(best_video)
        if not best_video_path or not os.path.exists(best_video_path):
            raise FileNotFoundError(
                f"Best video path not found for platform={platform}: {best_video_path}"
            )

        best_video = best_video_path

        if args.remix:
            best_video = merge_video_audio(best_video, audio_for_platform)

        # Pick a caption (you can also re-score captions later)
        captions = creative.get("captions", [])
        caption_final = captions[0]["text"] if captions else caption_seed

        print("✔ Best video:", best_video)
        print("✔ Best score:", round(best_score, 2))
        print("✔ Caption:", caption_final)

        results[platform] = {
            "best_video": best_video,
            "best_score": float(best_score),
            "caption": caption_final,
            "creative": creative,
        }

    # Save a JSON report for auditing
    out_dir = OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "run_report.json"
    report_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n✅ Done. Report saved to:", report_path)


if __name__ == "__main__":
    main()

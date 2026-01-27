from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import numpy as np
import soundfile as sf
import librosa
try:
    import scipy.signal
except Exception:
    scipy = None


@dataclass
class RemixPlan:
    # segment selection
    start_sec: float | None = None
    end_sec: float | None = None

    # tempo
    target_bpm: float | None = None
    max_time_stretch: float = 0.12  # max +/- 12%

    # tonal / dynamics
    bass_boost_db: float = 4.0
    presence_boost_db: float = 1.5
    limiter_ceiling: float = 0.98

    # optional: add a loop (legal sample only)
    drum_loop_path: str | None = None
    drum_mix_db: float = -10.0

    # output
    out_sr: int = 44100


class AudioRemixEngine:
    """
    Single-track remix/edit engine for short-form platforms.
    Works without stems: best-cut + mild tempo shift + EQ + limiter + optional loop overlay.
    """

    def load(self, audio_path: str, sr: int = 44100):
        y, sr = librosa.load(audio_path, sr=sr, mono=True)
        return y.astype(np.float32), sr

    def detect_bpm(self, y: np.ndarray, sr: int) -> float:
        """
        Use a lighter-weight BPM detection to avoid large memory use on long audio.
        Downsample and analyze only the first ~60s.
        """
        # limit to 60s to reduce memory
        max_sec = 60.0
        max_len = int(max_sec * sr)
        y_seg = y[:max_len]
        # downsample for beat tracking
        target_sr = 22050
        if sr != target_sr:
            y_seg = librosa.resample(y_seg, orig_sr=sr, target_sr=target_sr)
            sr = target_sr
        tempo, _ = librosa.beat.beat_track(y=y_seg, sr=sr)
        return float(tempo) if tempo and tempo > 0 else 120.0

    def pick_best_segment(self, y: np.ndarray, sr: int, duration_sec: float) -> tuple[float, float]:
        """
        Simple 'most energetic window' picker using RMS energy.
        """
        hop = 512
        frame = 2048
        rms = librosa.feature.rms(y=y, frame_length=frame, hop_length=hop)[0]
        times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)

        win = max(1, int(duration_sec / (hop / sr)))
        if len(rms) <= win:
            return 0.0, min(duration_sec, len(y) / sr)

        # rolling sum energy
        csum = np.cumsum(rms)
        sums = csum[win:] - csum[:-win]
        best_i = int(np.argmax(sums))
        start_t = float(times[best_i])
        end_t = start_t + duration_sec
        max_t = len(y) / sr
        if end_t > max_t:
            end_t = max_t
            start_t = max(0.0, end_t - duration_sec)
        return start_t, end_t

    def crop(self, y: np.ndarray, sr: int, start_sec: float, end_sec: float) -> np.ndarray:
        a = int(max(0.0, start_sec) * sr)
        b = int(min(end_sec, len(y) / sr) * sr)
        return y[a:b].copy()

    def time_stretch_to_bpm(self, y: np.ndarray, sr: int, src_bpm: float, target_bpm: float, max_stretch: float) -> np.ndarray:
        if not target_bpm or target_bpm <= 0:
            return y
        rate = target_bpm / max(src_bpm, 1e-6)  # >1 faster, <1 slower
        # clamp to avoid artifacts
        rate = float(np.clip(rate, 1.0 - max_stretch, 1.0 + max_stretch))
        # librosa: time_stretch works on STFT domain via phase vocoder; okay for small changes
        return librosa.effects.time_stretch(y, rate=rate).astype(np.float32)

    def _db_to_gain(self, db: float) -> float:
        return float(10 ** (db / 20.0))

    def eq_simple(self, y: np.ndarray, sr: int, bass_db: float, presence_db: float) -> np.ndarray:
        """
        Approx EQ: low-shelf-ish boost + gentle presence.
        Uses 2 filters: low-shelf approximation with lowpass + mix, and peaking-ish via bandpass mix.
        """
        if scipy is None:
            # Fallback: skip EQ if scipy is unavailable
            return y.astype(np.float32)
        y = y.astype(np.float32)

        # Lowpass for bass region (~120 Hz)
        cutoff_bass = 120.0 / (sr / 2.0)
        b_lp, a_lp = scipy.signal.butter(2, cutoff_bass, btype="low")
        bass = scipy.signal.lfilter(b_lp, a_lp, y)

        bass_gain = self._db_to_gain(bass_db) - 1.0
        y = y + bass_gain * bass

        # Presence band (~2.5 kHz)
        low = 1800.0 / (sr / 2.0)
        high = 3800.0 / (sr / 2.0)
        b_bp, a_bp = scipy.signal.butter(2, [low, high], btype="band")
        pres = scipy.signal.lfilter(b_bp, a_bp, y)

        pres_gain = self._db_to_gain(presence_db) - 1.0
        y = y + pres_gain * pres

        return y.astype(np.float32)

    def limiter(self, y: np.ndarray, ceiling: float = 0.98) -> np.ndarray:
        """
        Simple soft limiter: normalize + tanh saturation + ceiling clamp.
        """
        y = y.astype(np.float32)
        peak = float(np.max(np.abs(y)) + 1e-9)
        y = y / peak  # normalize to 1
        y = np.tanh(2.2 * y)  # soft clip
        y = np.clip(y, -ceiling, ceiling)
        return y.astype(np.float32)

    def overlay_loop(self, y: np.ndarray, sr: int, loop_path: str, mix_db: float) -> np.ndarray:
        loop, loop_sr = librosa.load(loop_path, sr=sr, mono=True)
        loop = loop.astype(np.float32)

        if len(loop) == 0:
            return y

        # tile loop to match length
        reps = int(np.ceil(len(y) / len(loop)))
        tiled = np.tile(loop, reps)[:len(y)]

        mix = self._db_to_gain(mix_db)  # negative db => quieter
        return (y + mix * tiled).astype(np.float32)

    def save(self, y: np.ndarray, sr: int, out_path: str):
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        sf.write(out_path, y, sr)

    def apply(self, audio_path: str, plan: RemixPlan, target_duration_sec: float) -> tuple[str, dict]:
        """
        Returns (out_audio_path, debug_info)
        """
        y, sr = self.load(audio_path, sr=plan.out_sr)
        src_bpm = self.detect_bpm(y, sr)

        # Segment selection
        if plan.start_sec is None or plan.end_sec is None:
            start_sec, end_sec = self.pick_best_segment(y, sr, target_duration_sec)
        else:
            start_sec, end_sec = plan.start_sec, plan.end_sec

        y_seg = self.crop(y, sr, start_sec, end_sec)

        # Tempo (small changes only)
        if plan.target_bpm:
            y_seg = self.time_stretch_to_bpm(y_seg, sr, src_bpm, plan.target_bpm, plan.max_time_stretch)

        # Optional drum loop overlay (LEGAL only)
        if plan.drum_loop_path:
            y_seg = self.overlay_loop(y_seg, sr, plan.drum_loop_path, plan.drum_mix_db)

        # EQ + limiter
        y_seg = self.eq_simple(y_seg, sr, plan.bass_boost_db, plan.presence_boost_db)
        y_seg = self.limiter(y_seg, plan.limiter_ceiling)

        out_base = Path(os.getenv("OUTPUT_DIR", "outputs"))
        out_audio = str(out_base / f"audio_adapted_{int(target_duration_sec)}s.wav")
        self.save(y_seg, sr, out_audio)

        dbg = {
            "src_bpm": src_bpm,
            "segment": {"start_sec": start_sec, "end_sec": end_sec},
            "target_bpm": plan.target_bpm,
            "out_sr": sr,
            "out_audio": out_audio,
        }
        return out_audio, dbg

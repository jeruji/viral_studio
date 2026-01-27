import librosa
import numpy as np

def extract_audio_features(audio_path: str) -> dict:
    y, sr = librosa.load(audio_path, sr=22050, mono=True, duration=120)

    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    rms = float(np.mean(librosa.feature.rms(y=y)))
    centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
    duration_sec = float(librosa.get_duration(y=y, sr=sr))

    return {
        "bpm": float(tempo),
        "duration_sec": duration_sec,
        "rms": rms,
        "spectral_centroid": centroid,
    }

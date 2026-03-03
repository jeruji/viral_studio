import librosa
import numpy as np

def extract_audio_features(audio_path: str) -> dict:
    y, sr = librosa.load(audio_path, sr=22050, mono=True, duration=120)

    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    rms_feat = librosa.feature.rms(y=y)
    centroid_feat = librosa.feature.spectral_centroid(y=y, sr=sr)
    bandwidth_feat = librosa.feature.spectral_bandwidth(y=y, sr=sr)
    rolloff_feat = librosa.feature.spectral_rolloff(y=y, sr=sr)
    zcr_feat = librosa.feature.zero_crossing_rate(y=y)
    chroma_feat = librosa.feature.chroma_stft(y=y, sr=sr)
    flatness_feat = librosa.feature.spectral_flatness(y=y)
    contrast_feat = librosa.feature.spectral_contrast(y=y, sr=sr)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    harmony_y = librosa.effects.harmonic(y)
    percep_y = librosa.effects.percussive(y)
    harmony_feat = librosa.feature.rms(y=harmony_y)
    percep_feat = librosa.feature.rms(y=percep_y)
    mfcc_feat = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)

    rms = float(np.mean(rms_feat))
    centroid = float(np.mean(centroid_feat))
    duration_sec = float(librosa.get_duration(y=y, sr=sr))

    # Heuristic proxies to align with music_genre.csv feature schema.
    loudness_db = float(20.0 * np.log10(max(rms, 1e-8)))
    energy = float(np.clip(rms * 3.0, 0.0, 1.0))
    flat = float(np.mean(flatness_feat))
    zcr = float(np.mean(zcr_feat))
    bw = float(np.mean(bandwidth_feat))
    bw_norm = float(np.clip(bw / 6000.0, 0.0, 1.0))
    centroid_norm = float(np.clip(centroid / 5000.0, 0.0, 1.0))
    onset_var = float(np.var(onset_env)) if onset_env.size else 0.0
    onset_norm = float(np.clip(onset_var / 100.0, 0.0, 1.0))
    tempo_norm = float(np.clip(float(tempo) / 200.0, 0.0, 1.0))
    speechiness = float(np.clip(0.55 * zcr + 0.25 * centroid_norm + 0.20 * onset_norm, 0.0, 1.0))
    acousticness = float(np.clip(0.65 * flat + 0.35 * (1.0 - energy), 0.0, 1.0))
    danceability = float(np.clip(0.45 * tempo_norm + 0.35 * onset_norm + 0.20 * (1.0 - zcr), 0.0, 1.0))
    harmonic = float(np.mean(harmony_feat))
    percussive = float(np.mean(percep_feat))
    instrumentalness = float(
        np.clip((harmonic / max(harmonic + percussive, 1e-8)) * (1.0 - speechiness), 0.0, 1.0)
    )
    liveness = float(np.clip(0.55 * bw_norm + 0.45 * zcr, 0.0, 1.0))
    contrast_mean = float(np.mean(contrast_feat))
    contrast_norm = float(np.clip(contrast_mean / 60.0, 0.0, 1.0))
    valence = float(np.clip(0.55 * energy + 0.30 * contrast_norm + 0.15 * danceability, 0.0, 1.0))

    feats = {
        # Existing runtime keys used by other parts of pipeline.
        "bpm": float(tempo),
        "duration_sec": duration_sec,
        "rms": rms,
        "spectral_centroid": centroid,
        # Features aligned to data/music_genre.csv for genre model.
        "acousticness": acousticness,
        "danceability": danceability,
        "duration_ms": float(duration_sec * 1000.0),
        "energy": energy,
        "instrumentalness": instrumentalness,
        "liveness": liveness,
        "loudness": loudness_db,
        "speechiness": speechiness,
        "tempo": float(tempo),
        "valence": valence,
        # GTZAN-compatible richer keys for genre model.
        "chroma_stft_mean": float(np.mean(chroma_feat)),
        "chroma_stft_var": float(np.var(chroma_feat)),
        "rms_mean": float(np.mean(rms_feat)),
        "rms_var": float(np.var(rms_feat)),
        "spectral_centroid_mean": float(np.mean(centroid_feat)),
        "spectral_centroid_var": float(np.var(centroid_feat)),
        "spectral_bandwidth_mean": float(np.mean(bandwidth_feat)),
        "spectral_bandwidth_var": float(np.var(bandwidth_feat)),
        "rolloff_mean": float(np.mean(rolloff_feat)),
        "rolloff_var": float(np.var(rolloff_feat)),
        "zero_crossing_rate_mean": float(np.mean(zcr_feat)),
        "zero_crossing_rate_var": float(np.var(zcr_feat)),
        "harmony_mean": float(np.mean(harmony_feat)),
        "harmony_var": float(np.var(harmony_feat)),
        "perceptr_mean": float(np.mean(percep_feat)),
        "perceptr_var": float(np.var(percep_feat)),
        "tempo": float(tempo),
    }

    for i in range(20):
        band = mfcc_feat[i]
        feats[f"mfcc{i+1}_mean"] = float(np.mean(band))
        feats[f"mfcc{i+1}_var"] = float(np.var(band))

    return feats

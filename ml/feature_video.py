import cv2
import numpy as np

def extract_video_features(video_path: str, sample_every_n_frames: int = 5) -> dict:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        # kalau video tidak ada / gagal dibuka, isi default
        return {
            "avg_brightness": 0.0,
            "cut_rate_per_min": 0.0,
            "has_faces": 0.0,
            "has_text_overlay": 0.0,
        }

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration_sec = frame_count / fps if fps > 0 else 0.0

    # Face detector (Haar)
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    prev_gray = None
    brightness_vals = []
    scene_changes = 0
    face_hits = 0
    sampled = 0

    # text overlay heuristic: banyak edge di area bawah + kontras tinggi (rough)
    text_overlay_hits = 0

    idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        idx += 1
        if idx % sample_every_n_frames != 0:
            continue

        sampled += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        brightness_vals.append(float(np.mean(gray)))

        # scene change heuristic (frame diff)
        if prev_gray is not None:
            diff = cv2.absdiff(gray, prev_gray)
            if float(np.mean(diff)) > 20.0:  # threshold kasar
                scene_changes += 1
        prev_gray = gray

        # faces
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        if len(faces) > 0:
            face_hits += 1

        # text overlay heuristic (bottom third edges)
        h, w = gray.shape
        bottom = gray[int(h * 0.65):, :]
        edges = cv2.Canny(bottom, 80, 160)
        edge_density = float(np.mean(edges > 0))
        if edge_density > 0.03:
            text_overlay_hits += 1

    cap.release()

    avg_brightness = float(np.mean(brightness_vals)) if brightness_vals else 0.0

    # cut_rate_per_min (approx)
    minutes = (duration_sec / 60.0) if duration_sec > 0 else 0.0
    cut_rate_per_min = float(scene_changes / minutes) if minutes > 0 else 0.0

    has_faces = 1.0 if sampled > 0 and (face_hits / sampled) > 0.05 else 0.0
    has_text_overlay = 1.0 if sampled > 0 and (text_overlay_hits / sampled) > 0.10 else 0.0

    return {
        "avg_brightness": avg_brightness,
        "cut_rate_per_min": cut_rate_per_min,
        "has_faces": has_faces,
        "has_text_overlay": has_text_overlay,
    }

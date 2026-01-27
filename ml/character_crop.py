from pathlib import Path
import os
import cv2

def extract_person_refs(
    video_path: str,
    out_dir: str | None = None,
    max_refs: int = 6,
    frame_stride: int = 15,
    min_face_ratio: float = 0.08,
    min_face_area_ratio: float = 0.005,
    use_person_fallback: bool = True,
    prefer_full_body: bool = True,
):
    if out_dir is None:
        out_dir = str(Path(os.getenv("OUTPUT_DIR", "outputs")) / "ref")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    eye_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_eye.xml"
    )
    hog = None
    if use_person_fallback:
        hog = cv2.HOGDescriptor()
        hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    refs = []
    f = 0
    saved = 0

    while saved < max_refs:
        ok, frame = cap.read()
        if not ok:
            break
        f += 1
        if f % frame_stride != 0:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        H, W = frame.shape[:2]
        min_w = int(W * min_face_ratio)
        min_h = int(H * min_face_ratio)
        min_area = int(W * H * min_face_area_ratio)

        # keep only reasonable face sizes to avoid false positives
        valid_faces = []
        for (x, y, w, h) in faces:
            if w < min_w or h < min_h:
                continue
            if (w * h) < min_area:
                continue
            valid_faces.append((x, y, w, h))

        if valid_faces:
            # keep faces that also have eyes (reduce false positives)
            eye_valid = []
            for (x, y, w, h) in valid_faces:
                face_roi = gray[y:y + h, x:x + w]
                if face_roi.size == 0:
                    continue
                eyes = eye_cascade.detectMultiScale(face_roi, 1.1, 4)
                if len(eyes) > 0:
                    eye_valid.append((x, y, w, h))
            if not eye_valid:
                continue
            # pick largest validated face
            x, y, w, h = max(eye_valid, key=lambda b: b[2] * b[3])
        elif hog is not None:
            # fallback: full-body person detection (helps when face is missed)
            rects, _ = hog.detectMultiScale(frame, winStride=(8, 8), padding=(8, 8), scale=1.05)
            if len(rects) == 0:
                continue
            # filter by size, aspect ratio, and centrality to avoid scenery
            cand = []
            for (x, y, w, h) in rects:
                area = w * h
                if area < (W * H * 0.10):
                    continue
                ar = w / float(h)
                if ar < 0.3 or ar > 0.9:
                    continue
                cx = x + w / 2.0
                cy = y + h / 2.0
                if not (W * 0.35 <= cx <= W * 0.65 and H * 0.25 <= cy <= H * 0.75):
                    continue
                cand.append((x, y, w, h))
            if not cand:
                continue
            x, y, w, h = max(cand, key=lambda b: b[2] * b[3])
        else:
            continue

        # expand crop; optionally bias downward to include full body/outfit
        if prefer_full_body:
            pad_x = int(w * 1.0)
            pad_top = int(h * 0.6)
            pad_bottom = int(h * 2.2)
            x0 = max(0, x - pad_x)
            y0 = max(0, y - pad_top)
            x1 = min(W, x + w + pad_x)
            y1 = min(H, y + h + pad_bottom)
        else:
            pad_x = int(w * 0.8)
            pad_y = int(h * 1.2)
            x0 = max(0, x - pad_x)
            y0 = max(0, y - pad_y)
            x1 = min(W, x + w + pad_x)
            y1 = min(H, y + h + pad_y)

        crop = frame[y0:y1, x0:x1]
        if crop.size == 0:
            continue

        saved += 1
        p = out / f"ref_{saved:02d}.jpg"
        cv2.imwrite(str(p), crop)
        refs.append(str(p))

    cap.release()
    return refs

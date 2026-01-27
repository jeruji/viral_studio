from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .db import Base, engine, get_db
from .models import User, Job
from .schemas import Token, UserCreate, UserOut, JobOut
from .auth import (
    create_access_token,
    get_current_user,
    require_admin,
    verify_password,
    get_password_hash,
)

app = FastAPI(title="Viral Studio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.post("/auth/login", response_model=Token)
def login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token({"sub": user.username, "role": user.role})
    return {"access_token": token, "token_type": "bearer"}


@app.post("/auth/bootstrap", response_model=UserOut)
def bootstrap_admin(user_in: UserCreate, db: Session = Depends(get_db)):
    if os.getenv("ALLOW_BOOTSTRAP", "false").lower() != "true":
        raise HTTPException(status_code=403, detail="Bootstrap disabled")
    if db.query(User).count() > 0:
        raise HTTPException(status_code=400, detail="Users already exist")
    user = User(
        username=user_in.username,
        password_hash=get_password_hash(user_in.password),
        role="admin",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.get("/users/me", response_model=UserOut)
def me(current: User = Depends(get_current_user)):
    return current


@app.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return db.query(User).all()


@app.post("/users", response_model=UserOut)
def create_user(user_in: UserCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    if db.query(User).filter(User.username == user_in.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    user = User(
        username=user_in.username,
        password_hash=get_password_hash(user_in.password),
        role=user_in.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.get("/jobs", response_model=list[JobOut])
def list_jobs(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    if current.role == "admin":
        return db.query(Job).order_by(Job.id.desc()).all()
    return db.query(Job).filter(Job.user_id == current.id).order_by(Job.id.desc()).all()


@app.get("/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if current.role != "admin" and job.user_id != current.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return job


def _run_pipeline(job_id: int, params: dict, input_paths: dict):
    db = next(get_db())
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return
        job.status = "running"
        job.updated_at = datetime.utcnow()
        db.commit()

        python_exe = Path("venv") / "Scripts" / "python.exe"
        if not python_exe.exists():
            python_exe = Path("python")

        cmd = [str(python_exe), "main.py"]
        cmd += ["--audio", input_paths["audio"]]
        cmd += ["--lyrics", input_paths["lyrics"]]
        cmd += ["--mood", params["mood"]]
        if input_paths.get("video"):
            cmd += ["--video", input_paths["video"]]
        if params.get("platforms"):
            cmd += ["--platforms", *params["platforms"]]
        if params.get("remix"):
            cmd += ["--remix"]
        if params.get("audio_style"):
            cmd += ["--audio-style", params["audio_style"]]
        if params.get("clip_seg_sec"):
            cmd += ["--clip-seg-sec", str(params["clip_seg_sec"])]
        if os.getenv("KIE_CALLBACK_URL"):
            cmd += ["--kie-callback-url", os.getenv("KIE_CALLBACK_URL")]

        log_dir = Path("outputs") / "jobs"
        job_out_dir = log_dir / f"job_{job_id}" / "run"
        job_out_dir.mkdir(parents=True, exist_ok=True)
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"job_{job_id}.log"
        with log_path.open("w", encoding="utf-8") as f:
            env = os.environ.copy()
            env["OUTPUT_DIR"] = str(job_out_dir)
            p = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, text=True, env=env)

        job.log_path = str(log_path)
        if p.returncode == 0:
            job.status = "success"
            report = job_out_dir / "run_report.json"
            if report.exists():
                report_out = log_dir / f"job_{job_id}_run_report.json"
                report_out.write_text(report.read_text(encoding="utf-8"), encoding="utf-8")
                job.report_path = str(report_out)
        else:
            job.status = "failed"
            job.error_message = f"Pipeline failed with code {p.returncode}"
        job.updated_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()


@app.post("/jobs", response_model=JobOut)
def create_job(
    background: BackgroundTasks,
    mood: str = Form(...),
    platforms: Optional[str] = Form(None),
    remix: bool = Form(False),
    audio_style: Optional[str] = Form(None),
    clip_seg_sec: Optional[float] = Form(None),
    audio: UploadFile = File(...),
    lyrics: UploadFile = File(...),
    video: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    upload_dir = Path("uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")

    audio_path = upload_dir / f"{current.id}_{ts}_{audio.filename}"
    lyrics_path = upload_dir / f"{current.id}_{ts}_{lyrics.filename}"
    audio_path.write_bytes(audio.file.read())
    lyrics_path.write_bytes(lyrics.file.read())

    video_path = None
    if video:
        video_path = upload_dir / f"{current.id}_{ts}_{video.filename}"
        video_path.write_bytes(video.file.read())

    params = {
        "mood": mood,
        "platforms": platforms.split(",") if platforms else [],
        "remix": remix,
        "audio_style": audio_style,
        "clip_seg_sec": clip_seg_sec,
    }
    inputs = {
        "audio": str(audio_path),
        "lyrics": str(lyrics_path),
        "video": str(video_path) if video_path else None,
    }

    job = Job(
        user_id=current.id,
        status="queued",
        params_json=json.dumps(params, ensure_ascii=False),
        inputs_json=json.dumps(inputs, ensure_ascii=False),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background.add_task(_run_pipeline, job.id, params, inputs)
    return job

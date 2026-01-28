# Viral Studio API (FastAPI)

## Features
- JWT auth (login, admin-only user creation)
- Roles: `admin` and `user`
- Job endpoint to run the existing `main.py` pipeline
- Upload endpoints for audio, lyrics, optional video

## Environment
Set these before running:
- `DATABASE_URL` (or `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DB`)
- `JWT_SECRET`
- `JWT_EXPIRE_MINUTES` (optional)
- `ALLOW_BOOTSTRAP=true` (one-time admin creation)

## Run
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## Notes
- This uses a simple synchronous background task to run `main.py`.
- Output files are written to `outputs/`, and job logs to `outputs/jobs/`.
- Concurrent runs may conflict with `outputs/run_report.json`.


Berikut langkah lengkap menjalankan seluruh platform (API + callback + frontend + pipeline):

1) Jalankan MySQL

Pastikan DB viral_studio sudah ada dan MySQL aktif di localhost (line 3306).
2) Start API (FastAPI)

.\start_api.ps1
3) Bootstrap admin (sekali saja)

curl -X POST http://localhost:8000/auth/bootstrap \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123","role":"admin"}'
Setelah itu, kamu bisa matikan ALLOW_BOOTSTRAP di .env.

4) Start callback server (ngrok)

uvicorn server_app:app --host 0.0.0.0 --port 8001
Lalu buka ngrok:

.\ngrok http 8001
Salin URL HTTPS ngrok, lalu set di command --kie-callback-url atau environment API jika mau.

5) Start frontend

cd frontend
npm install
npm run dev
Buka http://localhost:5173.

6) Login di frontend

Email/password sesuai admin di step 3.
7) Submit job

Upload audio + lyrics (+ video optional)
Isi mood, platforms, audio_style, clip_seg_sec
Submit
8) Cek status job

Panel status akan update saat kamu klik refresh
Log & report ada di path yang tampil

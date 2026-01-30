

import { useEffect, useMemo, useState } from "react";
import { clearToken, fetchJobs, getToken, login, setToken, submitJob } from "../api";
import { Job } from "../types";

const moodOptions = ["happy", "hype", "sad", "mellow", "nostalgic"];
const audioStyles = ["jedag_jedug", "tiktok_house", "mellow_rainy", "cinematic_epic", "lofi_chill"];

export default function App() {
  const [token, setLocalToken] = useState(getToken());
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loadingJobs, setLoadingJobs] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [contentType, setContentType] = useState("music");
  const [description, setDescription] = useState("");
  const [mood, setMood] = useState("hype");
  const [platforms, setPlatforms] = useState("tiktok");
  const [remix, setRemix] = useState(true);
  const [audioStyle, setAudioStyle] = useState("lofi_chill");
  const [clipSegSec, setClipSegSec] = useState("5");
  const [audio, setAudio] = useState<File | null>(null);
  const [lyrics, setLyrics] = useState<File | null>(null);
  const [video, setVideo] = useState<File | null>(null);

  const canSubmit = useMemo(() => {
    if (contentType === "music") return Boolean(audio && lyrics);
    return Boolean(description || video || audio || lyrics);
  }, [contentType, audio, lyrics, description, video]);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const data = await login(email, password);
      setToken(data.access_token);
      setLocalToken(data.access_token);
    } catch (err) {
      setError("Login gagal. Cek email/password.");
    }
  }

  async function handleSubmitJob(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const job = await submitJob({
        mood,
        platforms,
        remix,
        audio_style: audioStyle,
        clip_seg_sec: clipSegSec,
        content_type: contentType,
        description,
        audio,
        lyrics,
        video: video || undefined
      });
      setJobs((prev) => [job, ...prev]);
    } catch (err) {
      setError("Gagal submit job. Pastikan API berjalan.");
    }
  }

  async function refreshJobs() {
    setLoadingJobs(true);
    try {
      const data = await fetchJobs();
      setJobs(data);
    } catch (err) {
      setError("Gagal mengambil status job.");
    } finally {
      setLoadingJobs(false);
    }
  }

  useEffect(() => {
    if (token) {
      refreshJobs();
    }
  }, [token]);

  return (
    <div className="bg-light min-vh-100">
      <div className="container py-5">
        <header className="mb-4">
          <p className="text-uppercase text-primary small mb-1">Viral Studio</p>
          <h1 className="h2 mb-2">Creative pipeline control room</h1>
          <p className="text-muted mb-0">
            Login, upload assets, submit jobs, and monitor output from a single lightweight panel.
          </p>
        </header>

        {error && <div className="alert alert-danger">{error}</div>}

        {!token ? (
          <div className="row g-4">
            <div className="col-lg-6">
              <div className="card shadow-sm">
                <div className="card-body p-4">
                  <h2 className="h5 mb-3">Login</h2>
                  <form onSubmit={handleLogin} className="d-grid gap-3">
                    <input
                      className="form-control"
                      placeholder="Email"
                      value={email}
                      autoComplete="email"
                      onChange={(e) => setEmail(e.target.value)}
                    />
                    <input
                      className="form-control"
                      placeholder="Password"
                      type="password"
                      value={password}
                      autoComplete="current-password"
                      onChange={(e) => setPassword(e.target.value)}
                    />
                    <button className="btn btn-primary" type="submit">
                      Masuk
                    </button>
                  </form>
                </div>
              </div>
            </div>
            <div className="col-lg-6">
              <div className="card shadow-sm">
                <div className="card-body p-4">
                  <h3 className="h6 mb-3">Tips cepat</h3>
                  <ul className="small text-muted mb-0 d-grid gap-1">
                    <li>Set VITE_API_URL di .env frontend jika API bukan di localhost:8000.</li>
                    <li>Pastikan API dan callback server berjalan sebelum submit.</li>
                    <li>Gunakan clip seg 5 detik untuk batasan video generator.</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="row g-4">
            <div className="col-lg-8">
              <div className="card shadow-sm">
                <div className="card-body p-4">
                  <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
                    <h2 className="h5 mb-0">Submit Job</h2>
                    <button
                      className="btn btn-link p-0"
                      onClick={() => {
                        clearToken();
                        setLocalToken(null);
                      }}
                    >
                      Logout
                    </button>
                  </div>
                  <form onSubmit={handleSubmitJob} className="row g-3">
                    <div className="col-md-6">
                      <label className="form-label">Content Type</label>
                      <select className="form-select" value={contentType} onChange={(e) => setContentType(e.target.value)}>
                        <option value="music">music</option>
                        <option value="general">general</option>
                      </select>
                    </div>
                    <div className="col-md-6">
                      <label className="form-label">Mood</label>
                      <select className="form-select" value={mood} onChange={(e) => setMood(e.target.value)}>
                        {moodOptions.map((m) => (
                          <option key={m} value={m}>{m}</option>
                        ))}
                      </select>
                    </div>
                    <div className="col-md-6">
                      <label className="form-label">Platforms (comma separated)</label>
                      <input className="form-control" value={platforms} onChange={(e) => setPlatforms(e.target.value)} />
                    </div>
                    <div className="col-md-6">
                      <label className="form-label">Clip Segment (sec)</label>
                      <input className="form-control" value={clipSegSec} onChange={(e) => setClipSegSec(e.target.value)} />
                    </div>
                    <div className="col-md-6">
                      <label className="form-label">Audio Style</label>
                      <select className="form-select" value={audioStyle} onChange={(e) => setAudioStyle(e.target.value)}>
                        {audioStyles.map((s) => (
                          <option key={s} value={s}>{s}</option>
                        ))}
                      </select>
                    </div>
                    <div className="col-md-6 d-flex align-items-end">
                      <div className="form-check">
                        <input
                          className="form-check-input"
                          type="checkbox"
                          checked={remix}
                          onChange={(e) => setRemix(e.target.checked)}
                        />
                        <label className="form-check-label">Remix audio</label>
                      </div>
                    </div>

                    <div className="col-12">
                      <div className="border rounded-3 p-3 bg-white">
                        <div className="d-flex justify-content-between align-items-center mb-2">
                          <strong>Assets</strong>
                          <span className="text-muted small">
                            {contentType === "music" ? "Audio + lirik wajib" : "Video/teks opsional"}
                          </span>
                        </div>
                        <div className="row g-3">
                          <div className="col-md-4">
                            <label className="form-label">Audio {contentType === "music" ? "(required)" : "(optional)"}</label>
                            <input type="file" className="form-control" accept="audio/*" onChange={(e) => setAudio(e.target.files?.[0] || null)} />
                          </div>
                          <div className="col-md-4">
                            <label className="form-label">Lyrics {contentType === "music" ? "(required)" : "(optional)"}</label>
                            <input type="file" className="form-control" accept=".txt" onChange={(e) => setLyrics(e.target.files?.[0] || null)} />
                          </div>
                          <div className="col-md-4">
                            <label className="form-label">Video (optional)</label>
                            <input type="file" className="form-control" accept="video/*" onChange={(e) => setVideo(e.target.files?.[0] || null)} />
                          </div>
                          <div className="col-12">
                            <label className="form-label">Description (optional)</label>
                            <textarea className="form-control" rows={3} value={description} onChange={(e) => setDescription(e.target.value)} />
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="col-12">
                      <button className="btn btn-primary" type="submit" disabled={!canSubmit}>
                        Submit Job
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            </div>
            <div className="col-lg-4">
              <div className="card shadow-sm">
                <div className="card-body p-4">
                  <div className="d-flex justify-content-between align-items-center mb-3">
                    <h2 className="h6 mb-0">Status</h2>
                    <button className="btn btn-outline-secondary btn-sm" onClick={refreshJobs}>
                      {loadingJobs ? "Loading..." : "Refresh"}
                    </button>
                  </div>
                  {jobs.length === 0 && <p className="text-muted small">Belum ada job.</p>}
                  <div className="d-grid gap-2">
                    {jobs.map((job) => (
                      <div key={job.id} className="border rounded p-2 small">
                        <div className="d-flex justify-content-between">
                          <strong>Job #{job.id}</strong>
                          <span>{job.status}</span>
                        </div>
                        <div className="text-muted">{job.created_at}</div>
                        {job.error_message && <div className="text-danger">{job.error_message}</div>}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

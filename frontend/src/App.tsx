import { useEffect, useMemo, useState } from "react";
import { clearToken, fetchJobs, getToken, login, setToken, submitJob } from "./api";
import { Job } from "./types";

const moodOptions = ["happy", "hype", "sad", "mellow", "nostalgic"];
const audioStyles = ["jedag_jedug", "tiktok_house", "mellow_rainy", "cinematic_epic", "lofi_chill"];

export default function App() {
  const [token, setLocalToken] = useState(getToken());
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loadingJobs, setLoadingJobs] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [mood, setMood] = useState("hype");
  const [platforms, setPlatforms] = useState("tiktok");
  const [remix, setRemix] = useState(true);
  const [audioStyle, setAudioStyle] = useState("lofi_chill");
  const [clipSegSec, setClipSegSec] = useState("5");
  const [audio, setAudio] = useState<File | null>(null);
  const [lyrics, setLyrics] = useState<File | null>(null);
  const [video, setVideo] = useState<File | null>(null);

  const canSubmit = useMemo(() => {
    return Boolean(audio && lyrics);
  }, [audio, lyrics]);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const data = await login(email, password);
      setToken(data.access_token);
      setLocalToken(data.access_token);
    } catch (err) {
      setError("Login gagal. Cek username/password.");
    }
  }

  async function handleSubmitJob(e: React.FormEvent) {
    e.preventDefault();
    if (!audio || !lyrics) return;
    setError(null);
    try {
      const job = await submitJob({
        mood,
        platforms,
        remix,
        audio_style: audioStyle,
        clip_seg_sec: clipSegSec,
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
    <div className="min-h-screen px-6 py-10 text-slate-100">
      <div className="mx-auto max-w-6xl">
        <div className="flex flex-col gap-8">
          <header className="flex flex-col gap-2">
            <p className="text-sm uppercase tracking-[0.2em] text-emerald-300">Viral Studio</p>
            <h1 className="text-4xl md:text-5xl font-semibold font-display">
              Creative pipeline control room
            </h1>
            <p className="max-w-2xl text-slate-300">
              Login, upload assets, submit jobs, and monitor output from a single lightweight panel.
            </p>
          </header>

          {error && (
            <div className="rounded-xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-rose-200">
              {error}
            </div>
          )}

          {!token ? (
            <section className="grid gap-6 lg:grid-cols-[1.1fr_1fr]">
              <div className="rounded-3xl border border-white/10 bg-slate-900/60 p-8 shadow-xl">
                <h2 className="text-2xl font-semibold">Login</h2>
                <form onSubmit={handleLogin} className="mt-6 grid gap-4">
                  <input
                    className="w-full rounded-xl border border-white/10 bg-slate-950/60 px-4 py-3 text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-400"
                    placeholder="Email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                  <input
                    className="w-full rounded-xl border border-white/10 bg-slate-950/60 px-4 py-3 text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-400"
                    placeholder="Password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                  <button
                    className="rounded-xl bg-emerald-400 px-4 py-3 font-semibold text-slate-950 transition hover:brightness-110"
                    type="submit"
                  >
                    Masuk
                  </button>
                </form>
              </div>
              <div className="rounded-3xl border border-white/10 bg-slate-900/40 p-8">
                <h3 className="text-xl font-semibold">Tips</h3>
                <ul className="mt-4 space-y-3 text-sm text-slate-300">
                  <li>Set VITE_API_URL di .env frontend jika API bukan di localhost:8000.</li>
                  <li>Pastikan API dan callback server berjalan sebelum submit.</li>
                  <li>Gunakan clip seg 5 detik untuk batasan video generator.</li>
                </ul>
              </div>
            </section>
          ) : (
            <section className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
              <div className="rounded-3xl border border-white/10 bg-slate-900/60 p-8">
                <div className="flex items-center justify-between">
                  <h2 className="text-2xl font-semibold">Submit Job</h2>
                  <button
                    className="text-sm text-slate-300 hover:text-white"
                    onClick={() => {
                      clearToken();
                      setLocalToken(null);
                    }}
                  >
                    Logout
                  </button>
                </div>
                <form onSubmit={handleSubmitJob} className="mt-6 grid gap-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    <label className="grid gap-2 text-sm text-slate-300">
                      Mood
                      <select
                        value={mood}
                        onChange={(e) => setMood(e.target.value)}
                        className="rounded-xl border border-white/10 bg-slate-950/60 px-4 py-3 text-slate-100"
                      >
                        {moodOptions.map((m) => (
                          <option key={m} value={m}>
                            {m}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="grid gap-2 text-sm text-slate-300">
                      Platforms (comma separated)
                      <input
                        value={platforms}
                        onChange={(e) => setPlatforms(e.target.value)}
                        className="rounded-xl border border-white/10 bg-slate-950/60 px-4 py-3 text-slate-100"
                      />
                    </label>
                  </div>

                  <div className="grid gap-4 md:grid-cols-2">
                    <label className="grid gap-2 text-sm text-slate-300">
                      Audio Style
                      <select
                        value={audioStyle}
                        onChange={(e) => setAudioStyle(e.target.value)}
                        className="rounded-xl border border-white/10 bg-slate-950/60 px-4 py-3 text-slate-100"
                      >
                        {audioStyles.map((s) => (
                          <option key={s} value={s}>
                            {s}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="grid gap-2 text-sm text-slate-300">
                      Clip Segment (sec)
                      <input
                        value={clipSegSec}
                        onChange={(e) => setClipSegSec(e.target.value)}
                        className="rounded-xl border border-white/10 bg-slate-950/60 px-4 py-3 text-slate-100"
                      />
                    </label>
                  </div>

                  <label className="flex items-center gap-3 text-sm text-slate-300">
                    <input
                      type="checkbox"
                      checked={remix}
                      onChange={(e) => setRemix(e.target.checked)}
                    />
                    Remix audio
                  </label>

                  <div className="grid gap-4 md:grid-cols-3">
                    <label className="grid gap-2 text-sm text-slate-300">
                      Audio
                      <input type="file" accept="audio/*" onChange={(e) => setAudio(e.target.files?.[0] || null)} />
                    </label>
                    <label className="grid gap-2 text-sm text-slate-300">
                      Lyrics
                      <input type="file" accept=".txt" onChange={(e) => setLyrics(e.target.files?.[0] || null)} />
                    </label>
                    <label className="grid gap-2 text-sm text-slate-300">
                      Video (optional)
                      <input type="file" accept="video/*" onChange={(e) => setVideo(e.target.files?.[0] || null)} />
                    </label>
                  </div>

                  <button
                    className="rounded-xl bg-emerald-400 px-4 py-3 font-semibold text-slate-950 transition hover:brightness-110 disabled:opacity-50"
                    type="submit"
                    disabled={!canSubmit}
                  >
                    Submit Job
                  </button>
                </form>
              </div>

              <div className="rounded-3xl border border-white/10 bg-slate-900/40 p-6">
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-semibold">Status</h2>
                  <button
                    className="text-sm text-emerald-200 hover:text-emerald-100"
                    onClick={refreshJobs}
                  >
                    {loadingJobs ? "Loading..." : "Refresh"}
                  </button>
                </div>
                <div className="mt-4 space-y-4">
                  {jobs.length === 0 && (
                    <p className="text-sm text-slate-400">Belum ada job.</p>
                  )}
                  {jobs.map((job) => (
                    <div key={job.id} className="rounded-2xl border border-white/10 bg-slate-950/60 p-4">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-semibold">Job #{job.id}</span>
                        <span
                          className={`text-xs uppercase tracking-wide ${
                            job.status === "success"
                              ? "text-emerald-300"
                              : job.status === "failed"
                                ? "text-rose-300"
                                : "text-amber-300"
                          }`}
                        >
                          {job.status}
                        </span>
                      </div>
                      <p className="mt-2 text-xs text-slate-400">Created: {job.created_at}</p>
                      {job.error_message && (
                        <p className="mt-2 text-xs text-rose-300">{job.error_message}</p>
                      )}
                      <div className="mt-3 text-xs text-slate-300">
                        {job.report_path && <p>Report: {job.report_path}</p>}
                        {job.log_path && <p>Log: {job.log_path}</p>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </section>
          )}
        </div>
      </div>
    </div>
  );
}

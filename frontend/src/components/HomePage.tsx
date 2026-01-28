import React, { useState, useRef, useEffect } from "react";
import swal from "sweetalert";
import { useNavigate } from "react-router-dom";

const HomePage = () => {
    return(
<div></div>
    // <section className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
    //     <div className="rounded-3xl border border-white/10 bg-slate-900/60 p-8">
    //         <div className="flex items-center justify-between">
    //             <h2 className="text-2xl font-semibold">Submit Job</h2>
    //             <button
    //                 className="text-sm text-slate-300 hover:text-white"
    //                 onClick={() => {
    //                     clearToken();
    //                     setLocalToken(null);
    //                 }}
    //             >
    //                 Logout
    //             </button>
    //         </div>
    //         <form onSubmit={handleSubmitJob} className="mt-6 grid gap-4">
    //             <div className="grid gap-4 md:grid-cols-2">
    //                 <label className="grid gap-2 text-sm text-slate-300">
    //                     Mood
    //                     <select
    //                         value={mood}
    //                         onChange={(e) => setMood(e.target.value)}
    //                         className="rounded-xl border border-white/10 bg-slate-950/60 px-4 py-3 text-slate-100"
    //                     >
    //                         {moodOptions.map((m) => (
    //                             <option key={m} value={m}>
    //                                 {m}
    //                             </option>
    //                         ))}
    //                     </select>
    //                 </label>
    //                 <label className="grid gap-2 text-sm text-slate-300">
    //                     Platforms (comma separated)
    //                     <input
    //                         value={platforms}
    //                         onChange={(e) => setPlatforms(e.target.value)}
    //                         className="rounded-xl border border-white/10 bg-slate-950/60 px-4 py-3 text-slate-100"
    //                     />
    //                 </label>
    //             </div>

    //             <div className="grid gap-4 md:grid-cols-2">
    //                 <label className="grid gap-2 text-sm text-slate-300">
    //                     Audio Style
    //                     <select
    //                         value={audioStyle}
    //                         onChange={(e) => setAudioStyle(e.target.value)}
    //                         className="rounded-xl border border-white/10 bg-slate-950/60 px-4 py-3 text-slate-100"
    //                     >
    //                         {audioStyles.map((s) => (
    //                             <option key={s} value={s}>
    //                                 {s}
    //                             </option>
    //                         ))}
    //                     </select>
    //                 </label>
    //                 <label className="grid gap-2 text-sm text-slate-300">
    //                     Clip Segment (sec)
    //                     <input
    //                         value={clipSegSec}
    //                         onChange={(e) => setClipSegSec(e.target.value)}
    //                         className="rounded-xl border border-white/10 bg-slate-950/60 px-4 py-3 text-slate-100"
    //                     />
    //                 </label>
    //             </div>

    //             <label className="flex items-center gap-3 text-sm text-slate-300">
    //                 <input
    //                     type="checkbox"
    //                     checked={remix}
    //                     onChange={(e) => setRemix(e.target.checked)}
    //                 />
    //                 Remix audio
    //             </label>

    //             <div className="grid gap-4 md:grid-cols-3">
    //                 <label className="grid gap-2 text-sm text-slate-300">
    //                     Audio
    //                     <input type="file" accept="audio/*" onChange={(e) => setAudio(e.target.files?.[0] || null)} />
    //                 </label>
    //                 <label className="grid gap-2 text-sm text-slate-300">
    //                     Lyrics
    //                     <input type="file" accept=".txt" onChange={(e) => setLyrics(e.target.files?.[0] || null)} />
    //                 </label>
    //                 <label className="grid gap-2 text-sm text-slate-300">
    //                     Video (optional)
    //                     <input type="file" accept="video/*" onChange={(e) => setVideo(e.target.files?.[0] || null)} />
    //                 </label>
    //             </div>

    //             <button
    //                 className="rounded-xl bg-emerald-400 px-4 py-3 font-semibold text-slate-950 transition hover:brightness-110 disabled:opacity-50"
    //                 type="submit"
    //                 disabled={!canSubmit}
    //             >
    //                 Submit Job
    //             </button>
    //         </form>
    //     </div>

    //     <div className="rounded-3xl border border-white/10 bg-slate-900/40 p-6">
    //         <div className="flex items-center justify-between">
    //             <h2 className="text-xl font-semibold">Status</h2>
    //             <button
    //                 className="text-sm text-emerald-200 hover:text-emerald-100"
    //                 onClick={refreshJobs}
    //             >
    //                 {loadingJobs ? "Loading..." : "Refresh"}
    //             </button>
    //         </div>
    //         <div className="mt-4 space-y-4">
    //             {jobs.length === 0 && (
    //                 <p className="text-sm text-slate-400">Belum ada job.</p>
    //             )}
    //             {jobs.map((job) => (
    //                 <div key={job.id} className="rounded-2xl border border-white/10 bg-slate-950/60 p-4">
    //                     <div className="flex items-center justify-between">
    //                         <span className="text-sm font-semibold">Job #{job.id}</span>
    //                         <span
    //                             className={`text-xs uppercase tracking-wide ${job.status === "success"
    //                                     ? "text-emerald-300"
    //                                     : job.status === "failed"
    //                                         ? "text-rose-300"
    //                                         : "text-amber-300"
    //                                 }`}
    //                         >
    //                             {job.status}
    //                         </span>
    //                     </div>
    //                     <p className="mt-2 text-xs text-slate-400">Created: {job.created_at}</p>
    //                     {job.error_message && (
    //                         <p className="mt-2 text-xs text-rose-300">{job.error_message}</p>
    //                     )}
    //                     <div className="mt-3 text-xs text-slate-300">
    //                         {job.report_path && <p>Report: {job.report_path}</p>}
    //                         {job.log_path && <p>Log: {job.log_path}</p>}
    //                     </div>
    //                 </div>
    //             ))}
    //         </div>
    //     </div>
    // </section>
    )
};
export default HomePage;
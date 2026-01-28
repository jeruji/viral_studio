
// const HomePage = () => {
//     return(
// <div></div>
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
//     )
// };
// export default HomePage;

import React, { useState, useRef, useEffect } from "react";
import NavbarPage from "./Navbar";
import swal from "sweetalert";
import { useNavigate } from "react-router-dom";
import { submitJob } from "../api";
import { Job, moodOptions } from "../types";

const HomePage = () => {
    const [loading, setLoading] = useState<boolean>(true)
    const [lyricSelection, setLyricSelection] = useState("uploadLyric")
    const [description, setDescription] = useState<string>("")
    // const [dataAudio, setDataAudio] = useState<File>()
    // const [dataVideo, setDataVideo] = useState<File>()
    // const [dataImage, setDataImage] = useState<File[]>([])
    const [dataLyrics, setDataLyrics] = useState<File | string | null>()
    // const [dataMood, setDataMood] = useState<File | string>()
    const [error, setError] = useState<string | null>(null);
    const [mood, setMood] = useState("hype");
    const [platforms, setPlatforms] = useState("tiktok");
    const [remix, setRemix] = useState(true);
    const [audioStyle, setAudioStyle] = useState("lofi_chill");
    const [clipSegSec, setClipSegSec] = useState("5");
    const [audio, setAudio] = useState<File | null>(null);
    const [lyrics, setLyrics] = useState<File | null>(null);
    const [video, setVideo] = useState<File | null>(null);
    const [jobs, setJobs] = useState<Job[]>([]);
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
    useEffect(() => {
        console.log("print")
        setLoading(false)
    }, []);
    return (
        !loading && (
            <div className="container-fluid bg-white">
                <div className="row">
                    <div
                        className="col-2 p-0 m-0 d-none d-lg-block"
                        style={{ width: "80px" }}
                    >
                        <NavbarPage />
                    </div>

                    <div className="col-12 d-lg-none p-0 m-0">
                        <NavbarPage />
                    </div>
                    <div className="col">
                        <div className="row">
                            <div className="col-1"></div>
                            <div className="col-10 ">
                                <div
                                    className="row p-0 py-3"
                                    style={{ borderBottom: "1px solid black" }}
                                >
                                    <div className="col-5 p-0 m-0 d-flex align-items-center">
                                        <h3 className="font-mixta-sharp">Content Generator</h3>
                                    </div>
                                </div>
                                <div className="row py-2">
                                    <div className="col-3">
                                        Audio
                                    </div>
                                    <div className="col">
                                        <label htmlFor="music-upload" className="custom-file-label px-2">Choose File</label>
                                        <input type="file" hidden accept="audio/*" id="music-upload" onChange={(event) => {
                                            const files = event.target.files;
                                            if (!files || files.length === 0) return;

                                            const file = files[0];

                                            const reader = new FileReader();
                                            reader.readAsDataURL(file);
                                            reader.onloadend = () => {
                                                setAudio(file);
                                            };
                                        }} />
                                        <span >{audio ? audio.name : " No audio chosen"}</span>
                                    </div>
                                </div>
                                <div className="row py-2">
                                    <div className="col-3">
                                        Video
                                    </div>
                                    <div className="col">
                                        <label htmlFor="video-upload" className="custom-file-label px-2">Choose File</label>

                                        <input type="file" hidden accept="video/*" id="video-upload" onChange={(event) => {
                                            const files = event.target.files;
                                            if (!files || files.length === 0) return;

                                            const file = files[0];

                                            const reader = new FileReader();
                                            reader.readAsDataURL(file);

                                            reader.onloadend = () => {
                                                setVideo(file);
                                            };
                                        }} />
                                        <span >{video ? video.name : " No video chosen"}</span>
                                    </div>
                                </div>
                                {/* <div className="row py-2">
                                    <div className="col-3">
                                        Image
                                    </div>
                                    <div className="col">
                                        <label htmlFor="image-upload" className="custom-file-label px-2">Choose File</label>

                                        <input type="file" hidden accept="image/*" id="image-upload" multiple onChange={(event) => {
                                            const files = event.target.files;
                                            if (!files || files.length === 0) return;

                                            const file = files[0];

                                            const reader = new FileReader();
                                            reader.readAsDataURL(file);
                                            reader.onloadend = () => {
                                                setDataImage([...dataImage, file]);
                                            };
                                        }} />
                                        <span >{dataImage && dataImage.length > 0 ? dataImage.length + ' selected' : " No image chosen"}</span>
                                    </div>
                                </div> */}
                                <div className="row">
                                    <div className="col-3">Mood</div>
                                    <div className="col">
                                        <select
                                            value={mood}
                                            onChange={(e) => setMood(e.target.value)}
                                            className="custom-file-label"
                                        >
                                            {moodOptions.map((m) => (
                                                <option key={m} value={m}>
                                                    {m}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                </div>
                                <div className="row py-2">
                                    <div className="col-3">
                                        Lyrics
                                    </div>
                                    <div className="col">
                                        <div>
                                            <input type="radio" name="lyric" value="uploadLyric" checked={lyricSelection == "uploadLyric" ? true : false} onClick={(e) => { setLyricSelection('uploadLyric') }} />
                                            <label onClick={(e) => { setLyricSelection('uploadLyric'); setDataLyrics(null) }}>Upload txt</label>
                                        </div>

                                        <div>
                                            <input type="radio" name="lyric" value="pasteLyric" checked={lyricSelection == "pasteLyric" ? true : false} onClick={(e) => { setLyricSelection('pasteLyric') }} />
                                            <label onClick={(e) => { setLyricSelection('pasteLyric'); setDataLyrics("") }}>Copy and paste</label>
                                        </div>
                                    </div>
                                </div>
                                <div className="row">
                                    <div className="col-3">
                                        {" "}
                                    </div>
                                    <div className="col-6">
                                        {lyricSelection == "uploadLyric" ? <>
                                            <label htmlFor="lyric-upload" className="custom-file-label px-2">Choose File</label>

                                            <input type="file" hidden accept=".txt, text/plain" id="lyric-upload" onChange={(event) => {
                                                const files = event.target.files;
                                                if (!files || files.length === 0) return;

                                                const file = files[0];

                                                const reader = new FileReader();
                                                reader.readAsDataURL(file);
                                                reader.onloadend = () => {
                                                    setDataLyrics(file);
                                                };
                                            }} />
                                            <span >{dataLyrics && typeof (dataLyrics) !== "string" ? dataLyrics.name : " No file chosen"}</span>

                                        </>
                                            : <textarea placeholder="Paste lyrics here" className="w-100" style={{ minHeight: '200px' }} defaultValue={typeof (dataLyrics) == 'string' ? dataLyrics : ""} onChange={(e) => { setDataLyrics(e.currentTarget.value) }} />
                                        }
                                    </div>
                                </div>
                                <div className="row py-2">
                                    <div className="col-3">
                                        Description
                                    </div>
                                    <div className="col-6">
                                        <textarea defaultValue={description} placeholder="Add description" className="w-100" style={{ minHeight: '100px' }} onChange={(e) => { setDescription(e.currentTarget.value) }} />
                                    </div>
                                </div>

                                <div className="row pt-3">
                                    <div className="col">
                                        <button className="btn btn-primary">Generate Content</button>
                                    </div>
                                </div>
                            </div>

                            <div className="col-1"></div>
                        </div>
                    </div>
                </div>
            </div>
        )
    );
};
export default HomePage;

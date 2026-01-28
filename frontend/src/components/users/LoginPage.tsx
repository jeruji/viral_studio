// import { useEffect, useMemo, useState } from "react";
// import { clearToken, fetchJobs, getToken, login, setToken, submitJob } from "../../api";
// import { Job } from "../../types"

// const moodOptions = ["happy", "hype", "sad", "mellow", "nostalgic"];
// const audioStyles = ["jedag_jedug", "tiktok_house", "mellow_rainy", "cinematic_epic", "lofi_chill"];

// const Login = () => {
//   const [token, setLocalToken] = useState(getToken());
//   const [jobs, setJobs] = useState<Job[]>([]);
//   const [loadingJobs, setLoadingJobs] = useState(false);
//   const [error, setError] = useState<string | null>(null);

//   const [username, setUsername] = useState("");
//   const [password, setPassword] = useState("");

//   const [mood, setMood] = useState("hype");
//   const [platforms, setPlatforms] = useState("tiktok");
//   const [remix, setRemix] = useState(true);
//   const [audioStyle, setAudioStyle] = useState("lofi_chill");
//   const [clipSegSec, setClipSegSec] = useState("5");
//   const [audio, setAudio] = useState<File | null>(null);
//   const [lyrics, setLyrics] = useState<File | null>(null);
//   const [video, setVideo] = useState<File | null>(null);

//   const canSubmit = useMemo(() => {
//     return Boolean(audio && lyrics);
//   }, [audio, lyrics]);

//   async function handleLogin(e: React.FormEvent) {
//     e.preventDefault();
//     setError(null);
//     try {
//       const data = await login(username, password);
//       setToken(data.access_token);
//       setLocalToken(data.access_token);
//     } catch (err) {
//       setError("Login gagal. Cek username/password.");
//     }
//   }

//   async function handleSubmitJob(e: React.FormEvent) {
//     e.preventDefault();
//     if (!audio || !lyrics) return;
//     setError(null);
//     try {
//       const job = await submitJob({
//         mood,
//         platforms,
//         remix,
//         audio_style: audioStyle,
//         clip_seg_sec: clipSegSec,
//         audio,
//         lyrics,
//         video: video || undefined
//       });
//       setJobs((prev) => [job, ...prev]);
//     } catch (err) {
//       setError("Gagal submit job. Pastikan API berjalan.");
//     }
//   }

//   async function refreshJobs() {
//     setLoadingJobs(true);
//     try {
//       const data = await fetchJobs();
//       setJobs(data);
//     } catch (err) {
//       setError("Gagal mengambil status job.");
//     } finally {
//       setLoadingJobs(false);
//     }
//   }

//   useEffect(() => {
//     if (token) {
//       refreshJobs();
//     }
//   }, [token]);

//   return (
//     <div className="min-h-screen px-6 py-10 text-slate-100">
//       <div className="mx-auto max-w-6xl">
//         <div className="flex flex-col gap-8">
//           <header className="flex flex-col gap-2">
//             <p className="text-sm uppercase tracking-[0.2em] text-emerald-300">Viral Studio</p>
//             <h1 className="text-4xl md:text-5xl font-semibold font-display">
//               Creative pipeline control room
//             </h1>
//             <p className="max-w-2xl text-slate-300">
//               Login, upload assets, submit jobs, and monitor output from a single lightweight panel.
//             </p>
//           </header>

//           {error && (
//             <div className="rounded-xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-rose-200">
//               {error}
//             </div>
//           )}

//           {!token && (
//             <section className="grid gap-6 lg:grid-cols-[1.1fr_1fr]">
//               <div className="rounded-3xl border border-white/10 bg-slate-900/60 p-8 shadow-xl">
//                 <h2 className="text-2xl font-semibold">Login</h2>
//                 <form onSubmit={handleLogin} className="mt-6 grid gap-4">
//                   <input
//                     className="w-full rounded-xl border border-white/10 bg-slate-950/60 px-4 py-3 text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-400"
//                     placeholder="Username"
//                     value={username}
//                     onChange={(e) => setUsername(e.target.value)}
//                   />
//                   <input
//                     className="w-full rounded-xl border border-white/10 bg-slate-950/60 px-4 py-3 text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-400"
//                     placeholder="Password"
//                     type="password"
//                     value={password}
//                     onChange={(e) => setPassword(e.target.value)}
//                   />
//                   <button
//                     className="rounded-xl bg-emerald-400 px-4 py-3 font-semibold text-slate-950 transition hover:brightness-110"
//                     type="submit"
//                   >
//                     Masuk
//                   </button>
//                 </form>
//               </div>
//               <div className="rounded-3xl border border-white/10 bg-slate-900/40 p-8">
//                 <h3 className="text-xl font-semibold">Tips</h3>
//                 <ul className="mt-4 space-y-3 text-sm text-slate-300">
//                   <li>Set VITE_API_URL di .env frontend jika API bukan di localhost:8000.</li>
//                   <li>Pastikan API dan callback server berjalan sebelum submit.</li>
//                   <li>Gunakan clip seg 5 detik untuk batasan video generator.</li>
//                 </ul>
//               </div>
//             </section>
//           ) }
//         </div>
//       </div>
//     </div>
//   );
// }

// export default Login;

import React, {useState } from "react";
import { useNavigate } from "react-router-dom";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faEye, faEyeSlash } from "@fortawesome/free-solid-svg-icons";
import {  getToken, login, setToken } from "../../api";
const Login = () => {
    const [showPassword, setShowPassword] = useState<boolean>(false);
    const navigate = useNavigate();

    const [token, setLocalToken] = useState(getToken());
    const [error, setError] = useState<string | null>(null);

    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");


    async function handleLogin(e: React.FormEvent) {
        e.preventDefault();
        setError(null);
        try {
            const data = await login(username, password);
            setToken(data.access_token);
            setLocalToken(data.access_token);
            if (data.access_token) {
                navigate('/home')
            }
        } catch (err) {
            setError("Login gagal. Cek username/password.");
        }
    }

    return (
        <div className="container-fluid bg-white">
            <div className="row d-flex align-items-center vh-100">
                <div className="col-lg-5 d-none d-lg-block ps-4">
                    <div className="vertical-center">
                        <img
                            src={"/images/gdp-logo.svg"}
                            className="w-25"
                        ></img>
                        <h3
                            className="font-mixta-sharp color-black pt-3"
                            style={{ fontSize: "45px", lineHeight: "45px" }}
                        >
                            Viral Studio
                        </h3>
                    </div>
                </div>
                <div className="col-lg-7 col-md-12 font-mixta-sharp font-16 ">
                    <div className="row ">
                        <div className="col-lg-3 col"></div>
                        <div className="col-lg-7 col-10 ">
                            <div className="vertical-center ">
                                <div className=" d-lg-none">
                                    <div className="text-center">
                                        <img
                                            src={"/images/gdp-logo.svg"}
                                            className="w-25"
                                        ></img>
                                    </div>
                                </div>

                                <div className="row pb-3 d-lg-none">
                                    <h3 className="text-center">Viral Studio</h3>
                                </div>
                                <div className="border-input">
                                    <div className="row">
                                        <p className="p-0 m-0">Email Address</p>
                                    </div>
                                    <div className="row">
                                        <input
                                            placeholder="Enter your email"
                                            className="input-main"
                                            onChange={(e) => {
                                                setUsername(e.currentTarget.value);
                                            }}
                                        ></input>
                                    </div>
                                    <div className="row pt-2">
                                        <p className="p-0 m-0">Password</p>
                                    </div>
                                    <div className="row">

                                        <div className="position-relative w-100 p-0 m-0">
                                            <input
                                                type={showPassword ? "text" : "password"}
                                                className="input-main"
                                                id="password"
                                                value={password}
                                                placeholder="Password"
                                                onChange={(event) => setPassword(event.target.value)}
                                                onKeyDown={(e) => {
                                                    if (e.key === "Enter") handleLogin
                                                }}
                                            />

                                            <span
                                                className="position-absolute end-0 top-50 translate-middle-y pe-2"
                                                style={{ cursor: "pointer" }}
                                                onClick={() => setShowPassword(!showPassword)}
                                            >
                                                <FontAwesomeIcon
                                                    icon={showPassword ? faEye : faEyeSlash}
                                                />
                                            </span>
                                        </div>
                                    </div>
                                    <div className="row pt-3 ">
                                        <button className="btn-blue w-100 button-main" onClick={handleLogin}>
                                            Login
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div className="col-lg-2 col"></div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Login;

import React, { useState, useRef, useEffect } from "react";
import NavbarPage from "../Navbar";
import swal from "sweetalert";
import { useNavigate } from "react-router-dom";
import { audioStyles, Job, moodOptions, platformOptions, selectOptions } from "../../types"
import Select from "react-select";
import CreateService from "../service/CreateService";
import RetrieveService from "../service/RetrieveService";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faSpinner } from "@fortawesome/free-solid-svg-icons";
import { authHeader, getCurrentUserInfo } from "../service/AuthHeader";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const normalizeHashtags = (hashtags: any): string => {
    if (Array.isArray(hashtags)) return hashtags.join(", ");
    if (typeof hashtags === "string") return hashtags;
    return "";
};

const HomePage = () => {
    const [lyricSelection, setLyricSelection] = useState("uploadLyric")
    const [description, setDescription] = useState<string>("")
    const [lyrics, setLyrics] = useState<File | string | null>(null)
    const [error, setError] = useState<string | null>(null);
    const [mood, setMood] = useState("hype");
    const [contentType, setContentType] = useState("general");
    const [platforms, setPlatforms] = useState([]);
    const [remix, setRemix] = useState(true);
    const [generateAiVideo, setGenerateAiVideo] = useState(true);
    const [audioStyle, setAudioStyle] = useState("jazz");
    const [clipSegSec, setClipSegSec] = useState("5");
    const [audio, setAudio] = useState<File | null>(null);
    const [video, setVideo] = useState<File | null>(null);
    const [jobs, setJobs] = useState<any[]>([]);
    const [loadingJobs, setLoadingJobs] = useState<boolean>(false)
    const [statusJobs, setStatusJobs] = useState<string>("not available")
    const [jobId, setJobId] = useState<string>()
    const [isActiveResult, setIsActiveResult] = useState<string>("result-0")
    const navigate = useNavigate()

    async function handleDownloadVideo(jobId: string, platformKey: string, fallbackPath?: string) {
        try {
            const res = await fetch(`${API_URL}/jobs/${jobId}/download-video?platform=${encodeURIComponent(platformKey)}`, {
                headers: authHeader() as HeadersInit
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            const fallbackName = (fallbackPath || "").split(/[/\\\\]/).pop() || `${platformKey}.mp4`;
            a.download = fallbackName;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
        } catch (err) {
            swal("Download Video", "Failed to download video from API", "error");
        }
    }
    async function handleDownloadAudio(jobId: string, platformKey: string, fallbackPath?: string) {
        try {
            const res = await fetch(`${API_URL}/jobs/${jobId}/download-audio?platform=${encodeURIComponent(platformKey)}`, {
                headers: authHeader() as HeadersInit
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            const fallbackName = (fallbackPath || "").split(/[/\\\\]/).pop() || `${platformKey}.wav`;
            a.download = fallbackName;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
        } catch (err) {
            swal("Download Audio", "Failed to download produced audio from API", "error");
        }
    }

    const validationData = () => {
        const validateField = (fieldValue: string | number | any[] | boolean | File | null, fieldName: string) => {
            const isEmpty =
                fieldValue === null ||
                fieldValue === undefined ||
                (typeof fieldValue === "string" && fieldValue.trim().length === 0) ||
                (Array.isArray(fieldValue) && fieldValue.length === 0) ||
                (typeof fieldValue === "number" && fieldValue === 0);

            if (isEmpty) {
                swal({
                    title: "Empty Field",
                    text: `Please fill ${fieldName} section!`,
                    icon: "/images/icon-warning.svg",
                });
                return false;
            }

            return true;
        };
        const fieldsToValidate: { field: string | number | any[] | boolean | File | null; name: string }[] = [
            { field: platforms, name: "Platform" },
            { field: contentType, name: "Content Type" }

        ];
        if (contentType == "general") {
            fieldsToValidate.push({ field: description, name: "Description" }, { field: video, name: "video" })
        } else {
            fieldsToValidate.push({ field: mood, name: "Mood" }, { field: remix, name: "Remix" }, { field: audioStyle, name: "Audio Style" },
                { field: audio, name: "audio" }, { field: lyrics, name: "Lyrics" }
            )
            if (generateAiVideo) {
                fieldsToValidate.push({ field: clipSegSec, name: "Clip Seg Sec" })
            }
        }

        for (const item of fieldsToValidate) {
            if (!validateField(item.field, item.name)) {
                return false;
            }
        }
        return true;
    }
    const handleSubmitJob = async () => {
        const isDataValidate = validationData();
        if (!isDataValidate) return;

        try {
            const formData = new FormData();
            const platformValue = platforms.map((p: selectOptions) => p.value);

            formData.append("platforms", platformValue.join(","));
            formData.append("content_type", contentType);

            if (contentType === "general") {
                formData.append("description", description);
            } else {
                const safeAudioStyle = audioStyles.includes(audioStyle) ? audioStyle : "jazz";
                formData.append("mood", mood);
                formData.append("remix", remix.toString());
                formData.append("generate_ai_video", generateAiVideo.toString());
                formData.append("audio_style", safeAudioStyle);
                if (generateAiVideo) {
                    formData.append("clip_seg_sec", clipSegSec);
                }
                if (audio) formData.append("audio", audio);
                if (lyrics) formData.append("lyrics", lyrics);
            }

            if (video) formData.append("video", video);

            const res = await CreateService.createJob(formData);

            setJobs([]);
            setLoadingJobs(true);
            setStatusJobs(res.status);
            setJobId(res.id);

            swal({ title: "Content", "text": "Please wait until the result show . . .", timer: 5000 });
        } catch (err) {
            swal("Content", "Failed create new content", "error");
        }
    };

    useEffect(() => {
        if (!jobId) return;
        if (statusJobs !== "queued" && statusJobs !== "running") return;

        const intervalId = setInterval(() => {
            refreshJobs(jobId);
        }, 5000);

        return () => clearInterval(intervalId);
    }, [statusJobs, jobId]);

    useEffect(() => {
        const fetchUserInfo = async () => {
            try {
                const userInfo = await getCurrentUserInfo();
            } catch (err) {
                navigate("/login")
            }
        };

        fetchUserInfo();
    }, [])

    async function refreshJobs(id: string) {
        setLoadingJobs(true);
        try {
            const jobInfo = await RetrieveService.retrieveJobById(id);
            if (!jobInfo) {
                setLoadingJobs(false);
                return;
            }
            const status = String(jobInfo.status || "").toLowerCase();
            setStatusJobs(status || "running");

            if (status === "queued" || status === "running") {
                setLoadingJobs(true);
                return;
            }

            if (status === "failed") {
                setLoadingJobs(false);
                swal("Content", jobInfo.error_message || "Job failed", "error");
                return;
            }

            if (status === "success") {
                const res = await RetrieveService.retrieveResultJobsById(id);
                if (!res || res?.detail) {
                    setLoadingJobs(false);
                    return;
                }
                setJobs([res]);
                setStatusJobs("done");
                setLoadingJobs(false);
            }
        } catch (err) {
            setError("Gagal mengambil status job.");
            setLoadingJobs(false);
        }
    }
    return (

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
                                <div className="col-3">Platform</div>
                                <div className="col-6">
                                    <Select
                                        classNamePrefix="react-select-inside"
                                        isMulti={true}
                                        maxMenuHeight={250}
                                        onChange={(selected: any) => {
                                            setPlatforms(selected)
                                        }}
                                        options={platformOptions}
                                        value={platforms}
                                        placeholder="Select Portfolio"
                                    />
                                </div>
                            </div>
                            <div className="row ">
                                <div className="col-3">Content Type</div>
                                <div className="col">
                                    <select
                                        defaultValue={contentType}
                                        onChange={(e) => setContentType(e.target.value)}
                                        className="custom-file-label"
                                    >
                                        <option value={"music"}>Music</option>
                                        <option value={"general"}>General</option>
                                    </select>
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
                            {contentType == "general" ? <div className="row py-2">
                                <div className="col-3">
                                    Description
                                </div>
                                <div className="col-6">
                                    <textarea defaultValue={description} placeholder="Add description" className="w-100 ps-2" style={{ minHeight: '100px' }} onChange={(e) => { setDescription(e.currentTarget.value) }} />
                                </div>
                            </div> :
                                <>

                                    <div className="row ">
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
                                        <div className="col-3">Mood</div>
                                        <div className="col">
                                            <select
                                                value={mood}
                                                onChange={(e) => setMood(e.target.value)}
                                                className="custom-file-label"
                                            >
                                                {moodOptions.map((m) => (
                                                    <option key={m} value={m}>
                                                        {m.charAt(0).toUpperCase() + m.slice(1)}
                                                    </option>
                                                ))}
                                            </select>
                                        </div>
                                    </div>
                                    <div className="row">
                                        <div className="col-3">
                                        </div>
                                        <div className="col">
                                            <label className="flex items-center gap-3 text-sm text-slate-300">
                                                <input
                                                    type="checkbox"
                                                    checked={remix}
                                                    onChange={(e) => setRemix(e.target.checked)}
                                                />
                                                Remix audio
                                            </label>
                                        </div>
                                    </div>
                                    <div className="row">
                                        <div className="col-3">
                                        </div>
                                        <div className="col">
                                            <label className="flex items-center gap-3 text-sm text-slate-300">
                                                <input
                                                    type="checkbox"
                                                    checked={generateAiVideo}
                                                    onChange={(e) => setGenerateAiVideo(e.target.checked)}
                                                />
                                                Generate AI video
                                            </label>
                                        </div>
                                    </div>
                                    <div className="row py-2">
                                        <div className="col-3">Audio Style</div>
                                        <div className="col">
                                            <select
                                                value={audioStyle}
                                                onChange={(e) => setAudioStyle(e.target.value)}
                                                className="custom-file-label"
                                            >
                                                {audioStyles.map((s) => (
                                                    <option key={s} value={s}>
                                                        {(s.charAt(0).toUpperCase() + s.slice(1)).split("_").join(" ")}
                                                    </option>
                                                ))}
                                            </select>
                                        </div>
                                    </div>
                                    {generateAiVideo && (
                                        <div className="row ">
                                            <div className="col-3">Clip Segment (sec)</div>
                                            <div className="col">
                                                <input
                                                    value={clipSegSec}
                                                    onChange={(e) => setClipSegSec(e.target.value)}
                                                    className="border-radius-8 ps-2 input-130"
                                                ></input>
                                            </div>
                                        </div>
                                    )}
                                    <div className="row py-2">
                                        <div className="col-3">
                                            Lyrics
                                        </div>
                                        <div className="col">
                                            <div>
                                                <input type="radio" name="lyric" value="uploadLyric" checked={lyricSelection == "uploadLyric" ? true : false} onChange={(e) => { setLyricSelection('uploadLyric') }} />
                                                <label onClick={(e) => { setLyricSelection('uploadLyric'); setLyrics(null) }}>Upload txt</label>
                                            </div>

                                            <div>
                                                <input type="radio" name="lyric" value="pasteLyric" checked={lyricSelection == "pasteLyric" ? true : false} onChange={(e) => { setLyricSelection('pasteLyric') }} />
                                                <label onClick={(e) => { setLyricSelection('pasteLyric'); setLyrics("") }}>Copy and paste</label>
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
                                                        setLyrics(file);
                                                    };
                                                }} />
                                                <span >{lyrics && typeof (lyrics) !== "string" ? lyrics.name : " No file chosen"}</span>

                                            </>
                                                : <textarea placeholder="Paste lyrics here" className="w-100" style={{ minHeight: '200px' }} defaultValue={typeof (lyrics) == 'string' ? lyrics : ""} onChange={(e) => { setLyrics(e.currentTarget.value) }} />
                                            }
                                        </div>
                                    </div>
                                </>}


                            <div className="row py-3">
                                <div className="col">
                                    <button className="btn btn-primary" onClick={handleSubmitJob}>Generate Content</button>
                                </div>
                            </div>
                            <hr></hr>
                            <div className="row">
                                <div className="col">Result {loadingJobs && <FontAwesomeIcon icon={faSpinner} className="fa-spin" />}</div>
                            </div>
                            <div className="row py-3">
                                <div className="col">
                                    <div className="accordion">
                                        {jobs.map((job, jIndex) => {
                                            const platformEntries = Object.entries(job || {}).filter(([_, v]: any) => {
                                                return v && typeof v === "object" && (
                                                    "caption" in v ||
                                                    "best_video" in v ||
                                                    "ml_baseline" in v ||
                                                    "recommendations" in v
                                                );
                                            });
                                            return platformEntries.map(([platform], pIndex) => {
                                                const key = `${jIndex}-${platform}`

                                                return (
                                                    <div className="accordion-item" key={key}>
                                                        <h2 className="accordion-header">
                                                            <button
                                                                className={`accordion-button bg-blue ${isActiveResult == `result-${pIndex}` ? "" : "collapsed"}`}
                                                                type="button"
                                                                onClick={() => {
                                                                    if (isActiveResult == `result-${pIndex}`) {
                                                                        setIsActiveResult(`result-`)

                                                                    } else {
                                                                        setIsActiveResult(`result-${pIndex}`)
                                                                    }
                                                                }

                                                                }
                                                            >
                                                                {platform.split("_").join(" ").toUpperCase()}
                                                            </button>
                                                        </h2>

                                                        <div
                                                            className={`accordion-collapse collapse ${isActiveResult == `result-${pIndex}` ? "show" : ""
                                                                }`}
                                                        >
                                                            <div className="accordion-body">
                                                                {(() => {
                                                                    const resultItem = job?.[platform] || {};
                                                                    const bestVideoPath = resultItem?.["best_video"] || "";
                                                                    const firstCaption = resultItem?.creative?.captions?.[0];
                                                                    const hashtagsText = normalizeHashtags(firstCaption?.hashtags);
                                                                    const mlBaseline = resultItem?.["ml_baseline"] || {};
                                                                    const recommendations = Array.isArray(resultItem?.["recommendations"]) ? resultItem["recommendations"] : [];
                                                                    return (
                                                                        <>
                                                                <p>
                                                                    <strong>Caption:</strong>{" "}
                                                                    {resultItem?.caption || "-"}
                                                                </p>
                                                                <p>
                                                                    <strong>Hashtags: {" "}</strong>
                                                                    {hashtagsText}
                                                                </p>
                                                                <p>
                                                                    <strong>Best Video: {" "}</strong>
                                                                    {bestVideoPath || "-"}
                                                                    {bestVideoPath && jobId && (
                                                                        <button
                                                                            type="button"
                                                                            className="btn btn-sm btn-outline-primary ms-2"
                                                                            onClick={() => handleDownloadVideo(jobId, platform, bestVideoPath)}
                                                                        >
                                                                            Download
                                                                        </button>
                                                                    )}
                                                                </p>
                                                                {resultItem?.["produced_audio"] && (
                                                                    <p>
                                                                        <strong>Produced Audio: {" "}</strong>
                                                                        {resultItem["produced_audio"]}
                                                                        {jobId && (
                                                                            <button
                                                                                type="button"
                                                                                className="btn btn-sm btn-outline-primary ms-2"
                                                                                onClick={() => handleDownloadAudio(jobId, platform, resultItem["produced_audio"])}
                                                                            >
                                                                                Download
                                                                            </button>
                                                                        )}
                                                                    </p>
                                                                )}
                                                                {resultItem?.["manual_video_instruction"] && (
                                                                    <p>
                                                                        <strong>Manual Video Instruction: {" "}</strong>
                                                                        {resultItem["manual_video_instruction"]}
                                                                    </p>
                                                                )}
                                                                <p>
                                                                    <strong>Virality Score: {" "}</strong>
                                                                    {mlBaseline?.["virality_score"] ?? "-"}
                                                                </p>
                                                                <p>
                                                                    <strong>Audience: {" "}</strong>
                                                                    {String(mlBaseline?.["audience_label"] || "-").split("_").join(" ")}
                                                                </p>
                                                                <p>
                                                                    <strong>Genre: {" "}</strong>
                                                                    {mlBaseline?.["genre_label"] || "-"}
                                                                </p>
                                                                <strong>Recommendations: </strong>
                                                                <ul>
                                                                    {recommendations.map((recom: string, indexRecom: number) => {
                                                                        return (
                                                                            <li key={`recommendation-${platform}-${indexRecom}`}>
                                                                                {recom}
                                                                            </li>
                                                                        )
                                                                    })}
                                                                    {recommendations.length === 0 && <li>-</li>}
                                                                </ul>
                                                                        </>
                                                                    );
                                                                })()}
                                                            </div>
                                                        </div>
                                                    </div>
                                                )
                                            })
                                        })}
                                    </div>

                                </div>
                            </div>

                        </div>

                        <div className="col-1"></div>
                    </div>
                </div>
            </div>
        </div>

    );
};
export default HomePage;

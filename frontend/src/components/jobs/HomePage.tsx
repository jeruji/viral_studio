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
import { getCurrentUserInfo } from "../service/AuthHeader";
const HomePage = () => {
    const [lyricSelection, setLyricSelection] = useState("uploadLyric")
    const [description, setDescription] = useState<string>("")
    const [lyrics, setLyrics] = useState<File | string | null>(null)
    const [error, setError] = useState<string | null>(null);
    const [mood, setMood] = useState("hype");
    const [contentType, setContentType] = useState("general");
    const [platforms, setPlatforms] = useState([]);
    const [remix, setRemix] = useState(true);
    const [audioStyle, setAudioStyle] = useState("lofi_chill");
    const [clipSegSec, setClipSegSec] = useState("5");
    const [audio, setAudio] = useState<File | null>(null);
    const [video, setVideo] = useState<File | null>(null);
    const [jobs, setJobs] = useState<any[]>([]);
    const [loadingJobs, setLoadingJobs] = useState<boolean>(false)
    const [statusJobs, setStatusJobs] = useState<string>("not available")
    const [jobId, setJobId] = useState<string>()
    const [isActiveResult, setIsActiveResult] = useState<string>("result-0")
    const navigate = useNavigate()

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
            { field: mood, name: "Mood" },
            { field: contentType, name: "Content Type" },
            { field: video, name: "video" }

        ];
        if (contentType == "general") {
            fieldsToValidate.push({ field: description, name: "Description" })
        } else {
            fieldsToValidate.push({ field: remix, name: "Remix" }, { field: audioStyle, name: "Audio Style" }, { field: clipSegSec, name: "Clip Seg Sec" },
                { field: audio, name: "audio" }, { field: lyrics, name: "Lyrics" }
            )
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
            formData.append("mood", mood);
            formData.append("content_type", contentType);

            if (contentType === "general") {
                formData.append("description", description);
            } else {
                formData.append("remix", remix.toString());
                formData.append("audio_style", audioStyle);
                formData.append("clip_seg_sec", clipSegSec);
                if (audio) formData.append("audio", audio);
                if (lyrics) formData.append("lyrics", lyrics);
            }

            if (video) formData.append("video", video);

            const res = await CreateService.createJob(formData);

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
        if (statusJobs !== "queued") return;

        const intervalId = setInterval(() => {
            refreshJobs(jobId);
        }, 10000);

        return () => clearInterval(intervalId);
    }, [statusJobs]);

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
            await RetrieveService.retrieveResultJobsById(id).then((res: any) => {
                if (res?.detail) { return }
                setJobs([res])
                setStatusJobs("done")
                setLoadingJobs(false)
            })
        } catch (err) {
            setError("Gagal mengambil status job.");
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
                                        {jobs.map((job, jIndex) =>
                                            Object.keys(job).map((platform, pIndex) => {
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
                                                                <p>
                                                                    <strong>Caption:</strong>{" "}
                                                                    {job[platform].caption}
                                                                </p>
                                                                <p>
                                                                    <strong>Hashtags: {" "}</strong>
                                                                    {job[platform]['creative']['captions'][0]['hashtags'].join(", ")}
                                                                </p>
                                                                <p>
                                                                    <strong>Best Video: {" "}</strong>
                                                                    {job[platform]["best_video"]}
                                                                </p>
                                                            </div>
                                                        </div>
                                                    </div>
                                                )
                                            })
                                        )}
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

import React, { useState, useRef, useEffect } from "react";
import RetrieveService from "../service/RetrieveService";
import { Job, reportJob } from "../../types";
import NavbarPage from "../Navbar";
import { Modal, ModalBody, ModalFooter, ModalHeader } from "react-bootstrap";
const ListJobs = () => {
    const [loading, setLoading] = useState<boolean>(true)
    const [jobs, setJobs] = useState<reportJob[]>([])
    const [detailJob, setDetailJob] = useState<reportJob>()
    const [modalOpen, setModalOpen] = useState<boolean>(false)
    const toggleModal = () => setModalOpen(!modalOpen);
    useEffect(() => { getAllJobs() }, [])


    async function getAllJobs() {
        try {
            await RetrieveService.retrieveJobs().then((res: any) => {
                setJobs(res)
            })

        } catch (err) {
            swal("Jobs", "Failed retrieve jobs", "error")
        } finally {
            setLoading(false);
        }
    }
    return (
        !loading &&
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
                        <div className="col-10">

                            <div
                                className="row p-0 py-3"
                                style={{ borderBottom: "1px solid black" }}
                            >
                                <div className="col-5 p-0 m-0 d-flex align-items-center">
                                    <h3 className="font-mixta-sharp">List Jobs</h3>
                                </div>
                            </div>
                            <div className="row py-2">
                                <div className="col p-0 m-0">
                                    <div className="table-wrapper">
                                        <table className="table w-100 table-rounded">
                                            <thead>
                                                <tr className="text-center">
                                                    <th>Id</th>
                                                    <th>Status</th>
                                                    <th>Created</th>
                                                    <th>Meesage</th>
                                                    <th>Output</th>
                                                    <th>Detail</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {jobs.map((j, indexJ) => {
                                                    return (
                                                        <tr className="text-center" key={`item-${indexJ}`}>
                                                            <td className={`${j.status == "success" ? "success" : j.status == "failed" ? "failed" : "running"}`}>{j.id}</td>
                                                            <td className={`${j.status == "success" ? "success" : j.status == "failed" ? "failed" : "running"}`}>{j.status}</td>
                                                            <td className={`${j.status == "success" ? "success" : j.status == "failed" ? "failed" : "running"}`}>{j.created_at}</td>
                                                            <td className={`${j.status == "success" ? "success" : j.status == "failed" ? "failed" : "running"}`}>{j.error_message}</td>
                                                            <td className={`${j.status == "success" ? "success" : j.status == "failed" ? "failed" : "running"}`}>{j.log_path}</td>
                                                            <td className={`${j.status == "success" ? "success" : j.status == "failed" ? "failed" : "running"}`} onClick={(e) => { setDetailJob(j); setModalOpen(true) }}><button className="btn btn-active">view</button></td>
                                                        </tr>
                                                    )
                                                })}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div className="col-1"></div>
                        {
                            (modalOpen && detailJob) &&
                            <Modal
                                show={modalOpen}
                                aria-labelledby="contained-modal-title-vcenter"
                                centered={true}
                                size="lg"
                                onHide={toggleModal}
                                backdrop="static"
                                scrollable
                            >
                                <ModalHeader>
                                    <p>Jobs id : {detailJob?.id}</p>
                                </ModalHeader>
                                <ModalBody>
                                    {Object.entries(detailJob?.report_json).map(([platform, item]:any, indexResult:number) => {
                                        const key = `${item}-${platform}`
                                        return (
                                            <div className={`py-3 ${indexResult!=0 && "border-top"}`}>
                                                <h5><strong key={key}>{platform.split("_").join(" ").toUpperCase()}</strong></h5>
                                                <p>
                                                    <strong>Caption:</strong>{" "}
                                                    {item.caption}
                                                </p>
                                                <p>
                                                    <strong>Hashtags: {" "}</strong>
                                                    {item['creative']['captions'][0]['hashtags'].join(", ")}
                                                </p>
                                                <p>
                                                    <strong>Best Video: {" "}</strong>
                                                    {item["best_video"]}
                                                </p>
                                            </div>
                                        )
                                    })}

                                </ModalBody>
                                <ModalFooter>
                                    <button className="btn btn-active" onClick={toggleModal}>Close</button>
                                </ModalFooter>
                            </Modal>
                        }

                    </div>
                </div>
            </div>
        </div>
    )
}

export default ListJobs;
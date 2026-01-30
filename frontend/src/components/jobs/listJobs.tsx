import React, { useState, useRef, useEffect } from "react";
import RetrieveService from "../service/RetrieveService";
import { Job } from "../../types";
import NavbarPage from "../Navbar";
const ListJobs = () => {
    const [loading, setLoading] = useState<boolean>(true)
    const [jobs, setJobs] = useState<Job[]>([])
    useEffect(() => { getAllJobs() }, [])


    async function getAllJobs() {
        try {
            await RetrieveService.retrieveJobs().then((res: any) => {
                console.log(res)
                setJobs(res)
            })

        } catch (err) {
            swal("Jobs", "Failed retrieve jobs", "danger")
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
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {jobs.map((j, indexJ) => {
                                                    return (
                                                        <tr className="text-center">
                                                            <td>{j.id}</td>
                                                            <td>{j.status}</td>
                                                            <td>{j.created_at}</td>
                                                            <td>{j.error_message}</td>
                                                            <td>{j.log_path}</td>
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
                    </div>
                </div>
            </div>
        </div>
    )
}

export default ListJobs;
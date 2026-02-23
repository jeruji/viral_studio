import React, { useState, useRef, useEffect } from "react";
import RetrieveService from "../service/RetrieveService";
import { Job, userType } from "../../types";
import NavbarPage from "../Navbar";
import { useNavigate } from "react-router-dom";
const ListUsers = () => {
    const [loading, setLoading] = useState<boolean>(true)
    const [users, setUsers] = useState<userType[]>([])
    const navigate = useNavigate()
    useEffect(() => { getUsers(); setLoading(false) }, [])

    const getUsers = () => {
        RetrieveService.retrieveUsers().then((res) => {
            setUsers(res)
        }).catch((err) => {
            swal("Users", "Failed to load users", "error")
        })
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
                                    <h3 className="font-mixta-sharp">List Users</h3>
                                </div>
                                <div className="col p-0 m-0 text-end">
                                    <button className="btn btn-active" onClick={(e) => {
                                        navigate("/create-user")
                                    }}>+ Create user</button>
                                </div>
                            </div>
                            <div className="row py-2">
                                <div className="col p-0 m-0">
                                    <div className="table-wrapper">
                                        <table className="table w-100 table-rounded">
                                            <thead>
                                                <tr className="text-center">
                                                    {/* <th>Name</th> */}
                                                    <th className="bg-blue">Email</th>
                                                    <th className="bg-blue">Role</th>
                                                    <th className="bg-blue"></th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {users.map((u, indexU) => {
                                                    return (
                                                        <tr className="text-center" key={`user-${indexU}`}>
                                                            {/* <td>{"name"}</td> */}
                                                            <td>{u.email}</td>
                                                            <td>{u.role}</td>
                                                            <td>{ }</td>
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

export default ListUsers;
import React, { MutableRefObject, useEffect, useRef, useState } from "react";
import NavbarPage from "../Navbar";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faEye, faEyeSlash } from "@fortawesome/free-solid-svg-icons";
import { useNavigate } from "react-router-dom";
import CreateService from "../service/CreateService";
import { getCurrentUserInfo } from "../service/AuthHeader";


const CreateUser = () => {
    const [loading, setLoading] = useState(true);
    const [name, setName] = useState<string>("");
    const [email, setEmail] = useState<string>("");
    const [password, setPassword] = useState<string>("");
    const [showPassword, setShowPassword] = useState<boolean>(false);
    const [isAdmin, setIsAdmin] = useState<boolean>(false);
    const navigate = useNavigate()

    const submitUser = () => {
        CreateService.createUser(email, password, isAdmin ? "admin" : "user").then((res) => {
            swal("Create User", "Success create new user", "success")
            navigate("/list-user")
        }).catch((err) => {
            swal("Create User", "Failed create new user", "error")

        })
    }

    useEffect(() => {
        const fetchUserInfo = async () => {
            try {
                const userInfo = await getCurrentUserInfo();
                if (userInfo.role != "admin") {
                    swal(
                        "Unauthorized Access",
                        "You don’t have permission to access this page.",
                        "warning"
                    );
                    navigate("/list-user")
                }
            } catch (err) {
                console.error(err);
            }
        };

        fetchUserInfo();
    }, []);
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
                        <div className="col-10">

                            <div
                                className="row p-0 py-3"
                                style={{ borderBottom: "1px solid black" }}
                            >
                                <div className="col-5 p-0 m-0 d-flex align-items-center">
                                    <h3 className="font-mixta-sharp">Create new user</h3>
                                </div>
                            </div>

                            <div className="row pt-2">
                                <p className="p-0 m-0">Email</p>
                            </div>

                            <div className="row ">
                                <div className="col p-0 m-0">
                                    <input
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        className="w-50 input-white "
                                    ></input>
                                </div>
                            </div>
                            <div className="row py-2">
                                <p className="p-0 m-0">Password</p>
                            </div>
                            <div className="row ">

                                <div className="position-relative w-50 p-0 m-0">
                                    <input
                                        type={showPassword ? "text" : "password"}
                                        className="input-white "
                                        id="password"
                                        value={password}
                                        placeholder="Password"
                                        onChange={(event) => setPassword(event.target.value)}
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

                            <div className="row py-2">
                                <div className="col-1 p-0 m-0">
                                    <label>Role</label>
                                </div>
                                <div className="col">
                                    <label className="flex items-center gap-3 text-sm text-slate-300">
                                        <input
                                            type="checkbox"
                                            checked={isAdmin}
                                            onChange={(e) => setIsAdmin(e.target.checked)}
                                        />
                                        {" "} Admin
                                    </label>
                                </div>
                            </div>
                            <div className="row py-3">

                                <div className="col p-0 m-0">
                                    <button className="btn btn-inactive" onClick={() => { navigate("/list-user") }}>Cancel</button>
                                    <button className="btn btn-active ms-3" onClick={submitUser}>Create user</button>

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

export default CreateUser;
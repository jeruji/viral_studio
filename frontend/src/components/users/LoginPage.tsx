import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faEye, faEyeSlash } from "@fortawesome/free-solid-svg-icons";
import { getToken, login, setToken } from "../../api";
import CreateService from "../service/CreateService";
const Login = () => {
    const [showPassword, setShowPassword] = useState<boolean>(false);
    const navigate = useNavigate();
    const [error, setError] = useState<string | null>(null);

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    const handleLogin = async () => {
        setError(null);
        const formData = new FormData();
        formData.append("email", email)
        formData.append("password", password)
        const login = await CreateService
            .login(formData)
            .catch((error) => {
                swal("Log in failed!", error.message, "error");
                setError("Login gagal. Cek username/password.");
            });
        if (login?.access_token) {
            swal(
                "Log in success!",
                "Welcome to Viral Studio",
                "success",
                { timer: 1000 }
            ).then(() => {
                navigate('/home')
            });
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
                                                setEmail(e.currentTarget.value);
                                            }}
                                            defaultValue={email}
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
                                                    if (e.key === "Enter") {handleLogin()}
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

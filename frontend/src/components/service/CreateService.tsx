import axios from "axios";
import { authHeader } from "./AuthHeader";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";


const redirectToLogin = (response: string) => {
    if (response.includes("401")) {
        window.location.href = "/";
    }else{
        throw new Error(response);
    }
};

const login = (data: FormData) => {
    return axios
        .post(`${API_URL}/auth/login`, data, { headers: authHeader() })
        .then((response) => {
            if (response.data.access_token) {
                localStorage.setItem("user", JSON.stringify(response.data));
            }
            return response.data;
        })
        .catch((response) => {
            redirectToLogin(response.message);
        });
}
const createJob = (data: FormData) => {
    return axios
        .post(`${API_URL}/jobs`, data, { headers: authHeader() })
        .then((response) => {
            return response.data;
        })
        .catch((response) => {
            redirectToLogin(response.message);
        });
};

export default {
    login,
    createJob
}
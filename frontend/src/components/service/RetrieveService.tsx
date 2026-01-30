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

const retrieveJobs = () => {
    return axios
        .get(`${API_URL}/jobs`, { headers: authHeader() })
        .then((response) => {
            return response.data
        })
        .catch((response) => {
            redirectToLogin(response.message);
        });
};

export default {
    retrieveJobs
}

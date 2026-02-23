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
const retrieveUsers = () => {
    return axios
        .get(`${API_URL}/users`, { headers: authHeader() })
        .then((response) => {
            return response.data
        })
        .catch((response) => {
            redirectToLogin(response.message);
        });
};

const retrieveCurrentUser = () => {
    return axios
        .get(`${API_URL}/users/me`, { headers: authHeader() })
        .then((response) => {
            return response.data
        })
        .catch((response) => {
            redirectToLogin(response.message);
        });
};

const retrieveResultJobsById=(job_id:string)=>{
    return axios.get(`${API_URL}/jobs/${job_id}/result`, { headers: authHeader() })
        .then((response) => {
            return response.data
        })
        .catch((response) => {
            redirectToLogin(response.message);
        });
}

export default {
    retrieveJobs,
    retrieveUsers,
    retrieveCurrentUser,
    retrieveResultJobsById
}

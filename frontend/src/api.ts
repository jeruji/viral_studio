import { Job } from "./types";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const getToken = () => localStorage.getItem("vs_token");
export const setToken = (token: string) => localStorage.setItem("vs_token", token);
export const clearToken = () => localStorage.removeItem("vs_token");

export async function login(username: string, password: string) {
  const form = new FormData();
  form.append("username", username);
  form.append("password", password);
  const res = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    body: form
  });
  if (!res.ok) {
    throw new Error("Login failed");
  }
  return res.json();
}

export async function fetchJobs(): Promise<Job[]> {
  const token = getToken();
  const res = await fetch(`${API_URL}/jobs`, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });
  if (!res.ok) {
    throw new Error("Failed to load jobs");
  }
  return res.json();
}

export async function submitJob(payload: {
  mood: string;
  platforms: string;
  remix: boolean;
  audio_style?: string;
  clip_seg_sec?: string;
  audio: File;
  lyrics: File;
  video?: File;
}): Promise<Job> {
  const token = getToken();
  const form = new FormData();
  form.append("mood", payload.mood);
  if (payload.platforms) form.append("platforms", payload.platforms);
  if (payload.remix) form.append("remix", "true");
  if (payload.audio_style) form.append("audio_style", payload.audio_style);
  if (payload.clip_seg_sec) form.append("clip_seg_sec", payload.clip_seg_sec);
  form.append("audio", payload.audio);
  form.append("lyrics", payload.lyrics);
  if (payload.video) form.append("video", payload.video);

  const res = await fetch(`${API_URL}/jobs`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`
    },
    body: form
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Failed to submit job");
  }
  return res.json();
}

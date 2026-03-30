import axios from "axios";

const baseURL = process.env.REACT_APP_API_BASE_URL || "http://localhost:8000";

const API = axios.create({
  baseURL,
});

const PUBLIC_ENDPOINTS = ["/auth/login", "/auth/register", "/health"];

API.interceptors.request.use((config) => {
  const url = config.url || "";
  const isPublic = PUBLIC_ENDPOINTS.some((path) => url.startsWith(path));
  if (!isPublic) {
    const userId = sessionStorage.getItem("currentUserId");
    if (userId) {
      config.params = { ...(config.params || {}), user_id: Number(userId) };
    }
  }
  return config;
});

export default API;

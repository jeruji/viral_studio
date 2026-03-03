import RetrieveService from "./RetrieveService";

export const authHeader = () => {
    const userStr = localStorage.getItem("user");
    const baseHeaders: Record<string, string> = {
        // Prevent ngrok free-tier browser interstitial on API requests
        "ngrok-skip-browser-warning": "true",
    };
    if (!userStr) return baseHeaders;

    try {
        const token = JSON.parse(userStr);
        return token.access_token
            ? { ...baseHeaders, Authorization: `Bearer ${token.access_token}` }
            : baseHeaders;
    } catch {
        return baseHeaders;
    }
};

export const getCurrentUserInfo = () => {
    return RetrieveService.retrieveCurrentUser().then(res => res).catch((err) => { throw new Error("Failed to load user info"); })
}

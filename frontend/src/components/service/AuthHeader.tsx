import RetrieveService from "./RetrieveService";

export const authHeader = () => {
    const userStr = localStorage.getItem("user");
    if (!userStr) return {};

    try {
        const token = JSON.parse(userStr);
        return token.access_token
            ? { Authorization: `Bearer ${token.access_token}` }
            : {};
    } catch {
        return {};
    }
};

export const getCurrentUserInfo = () => {
    return RetrieveService.retrieveCurrentUser().then(res => res).catch((err) => { throw new Error("Failed to load user info"); })
}

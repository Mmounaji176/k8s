import { create } from 'zustand';
import { persist, createJSONStorage } from "zustand/middleware";
import Cookies from 'js-cookie';
import axios, { AxiosError } from 'axios';
import { jwtDecode } from 'jwt-decode';

axios.defaults.baseURL = import.meta.env.VITE_APP_BACKEND;

type userState = {
    id: string | null,
    username: string | null,
    userAvatar: string | null,
    isLoggedin: boolean,
    user: any,
}

type userActions = {
    login: (username: string, password: string) => Promise<boolean>,
    logout:  () => void,
    setAuthUser: (access_token: string, refresh_token: string) => void,
    getRefreshToken: () => Promise<any>,
    isAccessTokenExpired: (access_token: string) => boolean,
    checkAuthWtihRefresh: () => Promise<boolean>,
}
export const userStore = create<userState & userActions>()(

    persist((set, get) => ({
        isLoggedin: false,
        id: "",
        username: "",
        userAvatar: "",
        user: null,
        setAuthUser: (access_token, refresh_token) => {
            Cookies.set('access_token', access_token, {
                expires: 1,
                secure: false,
            });

            Cookies.set('refresh_token', refresh_token, {
                expires: 7,
                secure: false,
            });
        },

        getRefreshToken: async () => {
            try {
                const refresh_token = Cookies.get('refresh_token');
                if (!refresh_token)
                    throw "error"
                const response = await axios.post('api/token/refresh/', {
                    refresh: refresh_token,
                });
                return response;

            } catch (error) {
                if (error instanceof AxiosError)
                    return false
                else
                    return false
            }
        },
        checkAuthWtihRefresh: async () => {
            try {
                const refresh_token = Cookies.get('refresh_token');
                if (!refresh_token)
                    throw "error"
                const response = await axios.post('api/token/refresh/', {
                    refresh: refresh_token,
                });
                get().setAuthUser(response.data.access, response.data.refresh);
                return true;

            } catch (error) {
                if (error instanceof AxiosError)
                    return false
                else
                    return false
            }
        },
        isAccessTokenExpired: (accessToken) => {
            try {
                const decodedToken = jwtDecode(accessToken);
                if (decodedToken.exp !== undefined)
                    return decodedToken.exp < Date.now() / 1000;
                return true
            } catch (err) {
                return true;
            }
        },
        login: async (username: string, password: string) => {
            const res = await axios.post("/api/token/", { username: username, password: password })
            const data = res.data;
            get().setAuthUser(data.access, data.refresh);
            const userData = {
                id: data.id,
                isLoggedin: true,
                username: data.username,
                userAvatar: data.userAvatar,
               user: null,
            }

            set({ ...userData })
            return userData.isLoggedin;
        },
        logout: async() => {
            await Cookies.remove('access_token');
            await Cookies.remove('refresh_token');

        },

    }), {
        name: "userStore",
        storage: createJSONStorage(() => localStorage) as any,
    })
)


import axios from 'axios';

// Base URL for the Gateway
const BASE_URL = 'http://localhost:8000';

export const client = axios.create({
    baseURL: BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add a request interceptor to include the JWT token
client.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Add a response interceptor to handle errors
client.interceptors.response.use(
    (response) => response.data,
    (error) => {
        if (error.response) {
            // Server responded with a status code outside 2xx
            const customError = new Error(error.response.data.detail || error.response.statusText);
            customError.status = error.response.status;
            customError.detail = error.response.data;
            return Promise.reject(customError);
        }
        return Promise.reject(error);
    }
);

import axios from 'axios';

const REFRESH_ENDPOINT = '/api/token/refresh/';
const TOKEN_STORAGE_KEYS = { access: 'access', refresh: 'refresh' };

function getAccessToken() {
  return localStorage.getItem(TOKEN_STORAGE_KEYS.access);
}

function getRefreshToken() {
  return localStorage.getItem(TOKEN_STORAGE_KEYS.refresh);
}

function clearTokens() {
  localStorage.removeItem(TOKEN_STORAGE_KEYS.access);
  localStorage.removeItem(TOKEN_STORAGE_KEYS.refresh);
}

export function dispatchLogout() {
  clearTokens();
  window.dispatchEvent(new CustomEvent('auth:logout'));
}

const apiClient = axios.create({
  baseURL: '',
  headers: {
    'Content-Type': 'application/json',
  },
});

let isRefreshing = false;
let refreshPromise = null;

function doRefresh() {
  const refresh = getRefreshToken();
  if (!refresh) {
    return Promise.reject(new Error('No refresh token'));
  }
  return axios.post(REFRESH_ENDPOINT, { refresh }, { baseURL: '' });
}

apiClient.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status !== 401) {
      return Promise.reject(error);
    }

    if (originalRequest.url?.includes('/token/refresh/')) {
      dispatchLogout();
      return Promise.reject(error);
    }

    if (originalRequest._retry) {
      return Promise.reject(error);
    }

    if (!isRefreshing) {
      isRefreshing = true;
      refreshPromise = doRefresh()
        .then((res) => {
          const newAccess = res.data?.access;
          if (newAccess) {
            localStorage.setItem(TOKEN_STORAGE_KEYS.access, newAccess);
          }
          return newAccess;
        })
        .catch((refreshError) => {
          dispatchLogout();
          throw refreshError;
        })
        .finally(() => {
          isRefreshing = false;
          refreshPromise = null;
        });
    }

    return refreshPromise
      .then(() => {
        originalRequest._retry = true;
        originalRequest.headers.Authorization = `Bearer ${getAccessToken()}`;
        return apiClient(originalRequest);
      })
      .catch((e) => Promise.reject(e));
  }
);

export default apiClient;
export { getAccessToken, getRefreshToken, clearTokens };

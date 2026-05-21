import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';

const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
});

let isRefreshing = false;
let pendingQueue: Array<{
  resolve: () => void;
  reject: (error: unknown) => void;
}> = [];

const flushQueue = (error?: unknown) => {
  pendingQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else {
      resolve();
    }
  });
  pendingQueue = [];
};

const isAuthRoute = (url?: string) => {
  if (!url) return false;
  return [
    '/auth/login',
    '/auth/register',
    '/auth/refresh',
    '/auth/logout',
    '/auth/me',
    '/auth/verify',
  ].some((route) => url.includes(route));
};

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;

    if (!originalRequest || error.response?.status !== 401) {
      throw error;
    }

    if (originalRequest._retry || isAuthRoute(originalRequest.url)) {
      throw error;
    }

    originalRequest._retry = true;

    if (isRefreshing) {
      await new Promise<void>((resolve, reject) => {
        pendingQueue.push({ resolve, reject });
      });
      return api(originalRequest);
    }

    isRefreshing = true;

    try {
      await api.post('/auth/refresh');
      flushQueue();
      return api(originalRequest);
    } catch (refreshError) {
      flushQueue(refreshError);

      if (typeof window !== 'undefined') {
        const path = window.location.pathname;
        if (path !== '/autch' && path !== '/login') {
          window.location.replace('/autch');
        }
      }

      throw refreshError;
    } finally {
      isRefreshing = false;
    }
  }
);

export default api;

import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  withCredentials: true, // ОБЯЗАТЕЛЬНО для передачи кук
});

export default api;

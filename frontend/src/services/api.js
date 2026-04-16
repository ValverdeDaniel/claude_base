import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
});

// Attach token to every request
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

// On 401, clear token and redirect to login
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const login = (username, password) =>
  apiClient.post('/auth/login/', { username, password });

export const signup = (username, email, password) =>
  apiClient.post('/auth/signup/', { username, email, password });

export const logout = () =>
  apiClient.post('/auth/logout/');

export const getProfile = () =>
  apiClient.get('/auth/profile/');

export const changePassword = (oldPassword, newPassword) =>
  apiClient.post('/auth/change-password/', {
    old_password: oldPassword,
    new_password: newPassword,
  });

export const requestPasswordReset = (email) =>
  apiClient.post('/auth/request-password-reset/', { email });

export const resetPassword = (token, password) =>
  apiClient.post('/auth/reset-password/', { token, password });

// Notes
export const getNotes = () =>
  apiClient.get('/notes/');

export const createNote = (data) =>
  apiClient.post('/notes/', data);

export const updateNote = (id, data) =>
  apiClient.patch(`/notes/${id}/`, data);

export const deleteNote = (id) =>
  apiClient.delete(`/notes/${id}/`);

// Admin - Test Runner
export const getTests = () =>
  apiClient.get('/admin/tests/');

export const runTests = (testIds = []) =>
  apiClient.post('/admin/tests/run/', { test_ids: testIds });

export const getTestRunStatus = (runId) =>
  apiClient.get(`/admin/tests/runs/${runId}/status/`);

export const getTestRunDetail = (runId) =>
  apiClient.get(`/admin/tests/runs/${runId}/`);

export const getTestRunHistory = () =>
  apiClient.get('/admin/tests/runs/');

export const cancelTestRun = (runId) =>
  apiClient.post(`/admin/tests/runs/${runId}/cancel/`);

export default apiClient;

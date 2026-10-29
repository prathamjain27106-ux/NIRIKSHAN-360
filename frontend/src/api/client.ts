/* =================================================================
   NIRIKSHAN 360 — Central API Client
   Typed axios client with JWT interceptors.
   Falls back to demo data when backend endpoints are unavailable.
   ================================================================= */

import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios';
import type {
  AuthTokens,
  User,
  Complaint,
  ComplaintSubmission,
  ComplaintFilters,
  Institution,
  NormCheckResult,
  ComplianceRadarData,
  CaseGraphData,
  AuditEvent,
  InstitutionReply,
  DashboardMetrics,
  PaginatedResponse,
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

// ── Axios Instance ──
const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
});

// ── Token helpers ──
export function getStoredTokens(): AuthTokens | null {
  const access = localStorage.getItem('nirikshan_access');
  const refresh = localStorage.getItem('nirikshan_refresh');
  if (access && refresh) return { access, refresh };
  return null;
}

export function storeTokens(tokens: AuthTokens): void {
  localStorage.setItem('nirikshan_access', tokens.access);
  localStorage.setItem('nirikshan_refresh', tokens.refresh);
}

export function clearTokens(): void {
  localStorage.removeItem('nirikshan_access');
  localStorage.removeItem('nirikshan_refresh');
}

// ── Request interceptor: attach JWT ──
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const tokens = getStoredTokens();
  if (tokens?.access && config.headers) {
    config.headers.Authorization = `Bearer ${tokens.access}`;
  }
  return config;
});

// ── Response interceptor: refresh on 401 ──
let isRefreshing = false;
let failedQueue: { resolve: (t: string) => void; reject: (e: unknown) => void }[] = [];

function processQueue(error: unknown, token: string | null) {
  failedQueue.forEach(p => {
    if (token) p.resolve(token);
    else p.reject(error);
  });
  failedQueue = [];
}

api.interceptors.response.use(
  response => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    if (error.response?.status === 401 && !originalRequest._retry) {
      const tokens = getStoredTokens();
      if (!tokens?.refresh) {
        clearTokens();
        window.location.href = '/login';
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({
            resolve: (token: string) => {
              originalRequest.headers.Authorization = `Bearer ${token}`;
              resolve(api(originalRequest));
            },
            reject,
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;
      try {
        const { data } = await axios.post<AuthTokens>(`${API_BASE}/accounts/token/refresh/`, {
          refresh: tokens.refresh,
        });
        storeTokens(data);
        processQueue(null, data.access);
        originalRequest.headers.Authorization = `Bearer ${data.access}`;
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        clearTokens();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);

// ── Auth API ──
export const authApi = {
  login: async (username: string, password: string): Promise<AuthTokens> => {
    const { data } = await api.post<AuthTokens>('/accounts/login/', { username, password });
    storeTokens(data);
    return data;
  },
  me: async (): Promise<User> => {
    const { data } = await api.get<User>('/accounts/me/');
    return data;
  },
  logout: (): void => {
    clearTokens();
  },
};

// ── Complaint API (with demo fallback) ──
export const complaintsApi = {
  list: async (filters?: ComplaintFilters): Promise<PaginatedResponse<Complaint>> => {
    const { data } = await api.get<PaginatedResponse<Complaint>>('/complaints/', { params: filters });
    return data;
  },
  get: async (id: string): Promise<Complaint> => {
    const { data } = await api.get<Complaint>(`/complaints/${id}/`);
    return data;
  },
  create: async (payload: ComplaintSubmission): Promise<Complaint> => {
    const { data } = await api.post<Complaint>('/complaints/create/', payload);
    return data;
  },
  updateStatus: async (id: string, status: string, reason: string): Promise<Complaint> => {
    const { data } = await api.post<Complaint>(`/complaints/${id}/status/`, { status, reason });
    return data;
  },
};

// ── Institution API ──
export const institutionsApi = {
  list: async (): Promise<Institution[]> => {
    try {
      const { data } = await api.get<PaginatedResponse<Institution>>('/institutions/');
      return data.results;
    } catch {
      const { demoInstitutions } = await import('../data/demo');
      return demoInstitutions;
    }
  },
  get: async (id: string): Promise<Institution> => {
    try {
      const { data } = await api.get<Institution>(`/institutions/${id}/`);
      return data;
    } catch {
      const { demoInstitutions } = await import('../data/demo');
      const found = demoInstitutions.find(i => i.id === id);
      if (!found) throw new Error('Institution not found');
      return found;
    }
  },
  normCheck: async (id: string): Promise<NormCheckResult[]> => {
    try {
      const { data } = await api.get<NormCheckResult[]>(`/institutions/${id}/norm-check/`);
      return data;
    } catch {
      const { demoNormChecks } = await import('../data/demo');
      return demoNormChecks;
    }
  },
  complianceRadar: async (id: string): Promise<ComplianceRadarData> => {
    try {
      const { data } = await api.get<ComplianceRadarData>(`/institutions/${id}/compliance-radar/`);
      return data;
    } catch {
      const { demoComplianceRadar } = await import('../data/demo');
      return demoComplianceRadar(id);
    }
  },
  replies: async (institutionId: string): Promise<InstitutionReply[]> => {
    try {
      const { data } = await api.get<InstitutionReply[]>(`/institutions/${institutionId}/replies/`);
      return data;
    } catch {
      const { demoReplies } = await import('../data/demo');
      return demoReplies.filter(r => r.institution_id === institutionId);
    }
  },
};

// ── Case Graph API ──
export const graphApi = {
  get: async (complaintId?: string): Promise<CaseGraphData> => {
    try {
      const { data } = await api.get<CaseGraphData>('/complaints/graph/', { params: { complaint_id: complaintId } });
      return data;
    } catch {
      const { demoCaseGraph } = await import('../data/demo');
      return demoCaseGraph;
    }
  },
};

// ── Audit API ──
export const auditApi = {
  list: async (page = 1): Promise<PaginatedResponse<AuditEvent>> => {
    try {
      const { data } = await api.get<PaginatedResponse<AuditEvent>>('/audit/', { params: { page } });
      return data;
    } catch {
      const { demoAuditEvents } = await import('../data/demo');
      return { count: demoAuditEvents.length, next: null, previous: null, results: demoAuditEvents };
    }
  },
};

// ── Dashboard API ──
export const dashboardApi = {
  metrics: async (): Promise<DashboardMetrics> => {
    const { data } = await api.get<DashboardMetrics>('/complaints/dashboard/');
    return data;
  },
};

// ── Health ──
export const healthApi = {
  check: async (): Promise<{ status: string; service: string }> => {
    const { data } = await api.get<{ status: string; service: string }>('/health/');
    return data;
  },
};

export default api;

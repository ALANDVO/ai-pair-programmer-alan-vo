/**
 * Typed API Client for AI Pair Programmer
 */
import {
  CodebaseIndex,
  RefactorPlan,
  RefactorRequest,
  ApplyRequest,
  ApplyResult,
  BenchmarkSummary,
  StatsResponse,
  AuthUser
} from '../types';

const BASE_URL = '/api';

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };

  const response = await fetch(url, { ...options, headers });
  if (!response.ok) {
    const errorText = await response.text();
    let detail = `Request failed: ${response.statusText}`;
    try {
      const parsed = JSON.parse(errorText);
      if (parsed.detail) {
        detail = typeof parsed.detail === 'string' ? parsed.detail : JSON.stringify(parsed.detail);
      }
    } catch {
      if (errorText) detail = errorText;
    }
    throw new ApiError(response.status, detail);
  }

  return response.json();
}

export const apiClient = {
  getHealth: () => request<{ status: string; version: string; app_name: string }>('/health'),

  getStats: () => request<StatsResponse>('/stats'),

  getIndex: (path: string = '.', maxFiles: number = 25) =>
    request<CodebaseIndex>(`/index?path=${encodeURIComponent(path)}&max_files=${maxFiles}`),

  createPlan: (data: RefactorRequest) =>
    request<RefactorPlan>('/plan', {
      method: 'POST',
      body: JSON.stringify(data)
    }),

  getPlan: (planId: string) => request<RefactorPlan>(`/plan/${planId}`),

  applyPlan: (data: ApplyRequest) =>
    request<ApplyResult>('/apply', {
      method: 'POST',
      body: JSON.stringify(data)
    }),

  evaluateBenchmark: () =>
    request<BenchmarkSummary>('/evaluate', {
      method: 'POST'
    }),

  getBenchmark: () => request<BenchmarkSummary>('/benchmark'),

  getProfile: () => request<AuthUser>('/auth/me')
};

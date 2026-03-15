import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios'
import { ApiResponse, LoginParams, LoginResponse, User, PaginationParams, PaginationData, Anomaly, AnomalySeverity, AnomalyStatus, Metric, MetricQueryParams, RCAResult, RecoveryStrategy, RecoveryAction, DashboardStats } from '@types/index'

// 创建 axios 实例
const apiClient: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error: AxiosError<ApiResponse>) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('accessToken')
      localStorage.removeItem('refreshToken')
      window.location.href = '/login'
    }
    return Promise.reject(error.response?.data || error.message)
  }
)

// 认证相关 API
export const authApi = {
  login: (params: LoginParams) =>
    apiClient.post<ApiResponse<LoginResponse>>('/auth/login', params),

  logout: () =>
    apiClient.post<ApiResponse<void>>('/auth/logout'),

  refreshToken: (refreshToken: string) =>
    apiClient.post<ApiResponse<{ accessToken: string }>>('/auth/refresh', { refreshToken }),

  getCurrentUser: () =>
    apiClient.get<ApiResponse<User>>('/auth/me'),
}

// 仪表盘相关 API
export const dashboardApi = {
  getStats: () =>
    apiClient.get<ApiResponse<DashboardStats>>('/dashboard/stats'),
}

// 异常相关 API
export const anomalyApi = {
  getList: (params: PaginationParams & { severity?: AnomalySeverity; status?: AnomalyStatus; service?: string }) =>
    apiClient.get<ApiResponse<PaginationData<Anomaly>>>('/anomalies', { params }),

  getById: (id: string) =>
    apiClient.get<ApiResponse<Anomaly>>(`/anomalies/${id}`),

  acknowledge: (id: string) =>
    apiClient.post<ApiResponse<Anomaly>>(`/anomalies/${id}/acknowledge`),

  resolve: (id: string) =>
    apiClient.post<ApiResponse<Anomaly>>(`/anomalies/${id}/resolve`),

  ignore: (id: string) =>
    apiClient.post<ApiResponse<Anomaly>>(`/anomalies/${id}/ignore`),
}

// 指标相关 API
export const metricsApi = {
  query: (params: MetricQueryParams) =>
    apiClient.get<ApiResponse<Metric[]>>('/metrics/query', { params }),

  getLabels: () =>
    apiClient.get<ApiResponse<string[]>>('/metrics/labels'),

  getLabelValues: (label: string) =>
    apiClient.get<ApiResponse<string[]>>(`/metrics/labels/${label}/values`),
}

// RCA 相关 API
export const rcaApi = {
  getResult: (anomalyId: string) =>
    apiClient.get<ApiResponse<RCAResult>>(`/rca/${anomalyId}`),

  triggerAnalysis: (anomalyId: string) =>
    apiClient.post<ApiResponse<RCAResult>>('/rca/analyze', { anomalyId }),
}

// 恢复相关 API
export const recoveryApi = {
  getStrategies: () =>
    apiClient.get<ApiResponse<RecoveryStrategy[]>>('/recovery/strategies'),

  getActions: (params: PaginationParams) =>
    apiClient.get<ApiResponse<PaginationData<RecoveryAction>>>('/recovery/actions', { params }),

  execute: (anomalyId: string, strategyId: string, params?: Record<string, unknown>) =>
    apiClient.post<ApiResponse<RecoveryAction>>('/recovery/execute', { anomalyId, strategyId, params }),

  getActionStatus: (actionId: string) =>
    apiClient.get<ApiResponse<RecoveryAction>>(`/recovery/actions/${actionId}`),

  approve: (actionId: string) =>
    apiClient.post<ApiResponse<RecoveryAction>>(`/recovery/actions/${actionId}/approve`),

  cancel: (actionId: string) =>
    apiClient.post<ApiResponse<RecoveryAction>>(`/recovery/actions/${actionId}/cancel`),
}

// 用户管理 API
export const userApi = {
  getList: (params: PaginationParams) =>
    apiClient.get<ApiResponse<PaginationData<User>>>('/users', { params }),

  create: (data: Partial<User> & { password: string }) =>
    apiClient.post<ApiResponse<User>>('/users', data),

  update: (id: string, data: Partial<User>) =>
    apiClient.put<ApiResponse<User>>(`/users/${id}`, data),

  delete: (id: string) =>
    apiClient.delete<ApiResponse<void>>(`/users/${id}`),
}

export default apiClient

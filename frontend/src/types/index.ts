// 通用类型定义

export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

export interface PaginationParams {
  page: number
  pageSize: number
}

export interface PaginationData<T> {
  list: T[]
  total: number
  page: number
  pageSize: number
}

// 用户相关
export interface User {
  id: string
  username: string
  email: string
  role: 'admin' | 'operator' | 'viewer'
  avatar?: string
  createdAt: string
}

export interface LoginParams {
  username: string
  password: string
}

export interface LoginResponse {
  accessToken: string
  refreshToken: string
  user: User
}

// 异常相关
export type AnomalySeverity = 'critical' | 'high' | 'medium' | 'low'
export type AnomalyStatus = 'open' | 'acknowledged' | 'resolved' | 'ignored'

export interface Anomaly {
  id: string
  title: string
  description: string
  severity: AnomalySeverity
  status: AnomalyStatus
  service: string
  metric: string
  value: number
  expectedValue: number
  detectedAt: string
  resolvedAt?: string
  acknowledgedBy?: string
  acknowledgedAt?: string
  rcaResult?: RCAResult
}

// 指标相关
export interface Metric {
  name: string
  labels: Record<string, string>
  values: MetricValue[]
}

export interface MetricValue {
  timestamp: number
  value: number
}

export interface MetricQueryParams {
  query: string
  start: number
  end: number
  step?: number
}

// RCA 相关
export interface RCAResult {
  id: string
  anomalyId: string
  rootCause: string
  confidence: number
  serviceGraph?: ServiceGraph
  dimensionAttribution?: DimensionAttribution[]
  llmAnalysis?: string
  createdAt: string
}

export interface ServiceGraph {
  nodes: ServiceNode[]
  edges: ServiceEdge[]
}

export interface ServiceNode {
  id: string
  name: string
  status: 'normal' | 'warning' | 'error' | 'critical'
  metrics: Record<string, number>
}

export interface ServiceEdge {
  source: string
  target: string
  latency: number
  errorRate: number
}

export interface DimensionAttribution {
  dimension: string
  value: string
  contribution: number
  isAnomalous: boolean
}

// 恢复相关
export type RecoveryStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
export type RiskLevel = 'L1' | 'L2' | 'L3' | 'L4'

export interface RecoveryStrategy {
  id: string
  name: string
  description: string
  type: string
  riskLevel: RiskLevel
  parameters: Record<string, unknown>
}

export interface RecoveryAction {
  id: string
  anomalyId: string
  strategyId: string
  strategyName: string
  status: RecoveryStatus
  params: Record<string, unknown>
  result?: string
  error?: string
  executedBy?: string
  executedAt?: string
  completedAt?: string
  approvedBy?: string
  approvedAt?: string
}

// WebSocket 消息
export interface WebSocketMessage {
  type: 'anomaly_detected' | 'recovery_completed' | 'rca_completed' | 'ping' | 'pong'
  payload: unknown
  timestamp: number
}

// 仪表盘统计
export interface DashboardStats {
  totalAnomalies: number
  openAnomalies: number
  criticalAnomalies: number
  recoverySuccessRate: number
  recentAnomalies: Anomaly[]
  metricsOverview: {
    name: string
    value: number
    trend: number
  }[]
}

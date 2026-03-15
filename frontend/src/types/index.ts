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
  current_value: number
  expected_value: number
  detected_at: string
  resolved_at?: string
  acknowledged_by?: string
  acknowledged_at?: string
  rca_result?: RCAResult
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
  anomaly_id: string
  root_cause: string
  confidence: number
  service_graph?: ServiceGraph
  dimension_attribution?: DimensionAttribution[]
  llm_analysis?: string
  created_at: string
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
  error_rate: number
}

export interface DimensionAttribution {
  dimension: string
  value: string
  contribution: number
  is_anomalous: boolean
}

// 恢复相关
export type RecoveryStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
export type RiskLevel = 'L1' | 'L2' | 'L3' | 'L4'

export interface RecoveryStrategy {
  id: string
  name: string
  description: string
  type: string
  risk_level: RiskLevel
  parameters: Record<string, unknown>
}

export interface RecoveryAction {
  id: string
  anomaly_id: string
  strategy_id: string
  strategy_name: string
  status: RecoveryStatus
  params: Record<string, unknown>
  result?: string
  error?: string
  executed_by?: string
  executed_at?: string
  completed_at?: string
  approved_by?: string
  approved_at?: string
}

// WebSocket 消息
export interface WebSocketMessage {
  type: 'anomaly_detected' | 'recovery_completed' | 'rca_completed' | 'ping' | 'pong'
  payload: unknown
  timestamp: number
}

// 仪表盘统计
export interface DashboardStats {
  total_anomalies: number
  open_anomalies: number
  critical_anomalies: number
  recovery_success_rate: number
  recent_anomalies: Anomaly[]
  metrics_overview: {
    name: string
    value: number
    trend: number
  }[]
}

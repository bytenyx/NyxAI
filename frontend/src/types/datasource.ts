export interface DataSource {
  id: string
  type: 'prometheus' | 'influxdb' | 'loki' | 'jaeger'
  name: string
  url: string
  auth_type: 'none' | 'basic' | 'bearer' | 'api_key'
  auth_config?: {
    username?: string
    password?: string
    token?: string
    api_key?: string
  }
  status: 'connected' | 'disconnected' | 'error' | 'not_configured'
  last_check?: string
  error_message?: string
  created_at: string
  updated_at: string
}

export interface DataSourceCreate {
  type: 'prometheus' | 'influxdb' | 'loki' | 'jaeger'
  name: string
  url: string
  auth_type?: 'none' | 'basic' | 'bearer' | 'api_key'
  auth_config?: Record<string, string>
}

export interface DataSourceUpdate {
  name?: string
  url?: string
  auth_type?: string
  auth_config?: Record<string, string>
}

export interface DataSourceTestResult {
  success: boolean
  message: string
  latency_ms?: number
}

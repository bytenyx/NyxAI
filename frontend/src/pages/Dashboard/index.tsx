import { useEffect, useState } from 'react'
import { Row, Col, Card, Statistic, Table, Tag, Badge, Spin, Alert } from 'antd'
import {
  AlertOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  LineChartOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import { Area } from '@ant-design/charts'
import { useTranslation } from 'react-i18next'
import { dashboardApi } from '@services/api'
import { wsService } from '@services/websocket'
import { DashboardStats, Anomaly, AnomalySeverity } from '@types/index'
import dayjs from 'dayjs'
import styles from './styles.module.css'

const DashboardPage = () => {
  const { t } = useTranslation()
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const severityColors: Record<AnomalySeverity, string> = {
    critical: 'red',
    high: 'orange',
    medium: 'gold',
    low: 'green',
  }

  const fetchStats = async () => {
    try {
      setLoading(true)
      const response = await dashboardApi.getStats()
      setStats(response.data)
      setError(null)
    } catch (err) {
      setError(t('errors.fetchFailed'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStats()

    // 订阅实时更新
    const unsubscribeAnomaly = wsService.subscribe('anomaly_detected', () => {
      fetchStats()
    })

    const unsubscribeRecovery = wsService.subscribe('recovery_completed', () => {
      fetchStats()
    })

    // 定时刷新
    const interval = setInterval(fetchStats, 30000)

    return () => {
      unsubscribeAnomaly()
      unsubscribeRecovery()
      clearInterval(interval)
    }
  }, [t])

  const columns = [
    {
      title: t('anomaly.fields.title'),
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
    },
    {
      title: t('anomaly.fields.service'),
      dataIndex: 'service',
      key: 'service',
    },
    {
      title: t('anomaly.fields.severity'),
      dataIndex: 'severity',
      key: 'severity',
      render: (severity: AnomalySeverity) => (
        <Tag color={severityColors[severity]}>{t(`anomaly.severity.${severity}`)}</Tag>
      ),
    },
    {
      title: t('anomaly.fields.status'),
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        return <Badge color={status === 'open' ? 'red' : status === 'resolved' ? 'green' : 'orange'} text={t(`anomaly.status.${status}`)} />
      },
    },
    {
      title: t('anomaly.fields.detectedAt'),
      dataIndex: 'detected_at',
      key: 'detected_at',
      render: (time: string) => dayjs(time).format('MM-DD HH:mm'),
    },
  ]

  // 模拟趋势图数据
  const trendData = [
    { date: t('common.date') + ' 1', value: 12, type: t('dashboard.trend.anomalyCount') },
    { date: t('common.date') + ' 2', value: 8, type: t('dashboard.trend.anomalyCount') },
    { date: t('common.date') + ' 3', value: 15, type: t('dashboard.trend.anomalyCount') },
    { date: t('common.date') + ' 4', value: 6, type: t('dashboard.trend.anomalyCount') },
    { date: t('common.date') + ' 5', value: 10, type: t('dashboard.trend.anomalyCount') },
    { date: t('common.date') + ' 6', value: 5, type: t('dashboard.trend.anomalyCount') },
    { date: t('common.date') + ' 7', value: 7, type: t('dashboard.trend.anomalyCount') },
  ]

  const areaConfig = {
    data: trendData,
    xField: 'date',
    yField: 'value',
    smooth: true,
    areaStyle: {
      fill: 'l(270) 0:#ffffff 0.5:#e6f7ff 1:#1890ff',
    },
    height: 200,
  }

  if (error) {
    return (
      <Alert
        message={t('common.error')}
        description={error}
        type="error"
        showIcon
        action={
          <ReloadOutlined onClick={fetchStats} style={{ cursor: 'pointer' }} />
        }
      />
    )
  }

  return (
    <Spin spinning={loading}>
      <div className={styles.container}>
        {/* 统计卡片 */}
        <Row gutter={16} className={styles.statsRow}>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title={t('dashboard.stats.totalAnomalies')}
                value={stats?.total_anomalies || 0}
                prefix={<AlertOutlined />}
                valueStyle={{ color: '#cf1322' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title={t('dashboard.stats.openAnomalies')}
                value={stats?.open_anomalies || 0}
                prefix={<ExclamationCircleOutlined />}
                valueStyle={{ color: '#fa8c16' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title={t('dashboard.stats.criticalAnomalies')}
                value={stats?.critical_anomalies || 0}
                prefix={<LineChartOutlined />}
                valueStyle={{ color: '#ff4d4f' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title={t('dashboard.stats.recoverySuccessRate')}
                value={stats?.recovery_success_rate || 0}
                suffix="%"
                prefix={<CheckCircleOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
        </Row>

        {/* 趋势图和最近异常 */}
        <Row gutter={16} className={styles.contentRow}>
          <Col xs={24} lg={12}>
            <Card title={t('dashboard.trend.title')} className={styles.chartCard}>
              <Area {...areaConfig} />
            </Card>
          </Col>
          <Col xs={24} lg={12}>
            <Card
              title={t('dashboard.recentAnomalies')}
              extra={<a href="#/anomalies">{t('dashboard.viewAll')}</a>}
              className={styles.tableCard}
            >
              <Table
                dataSource={stats?.recent_anomalies || []}
                columns={columns}
                rowKey="id"
                pagination={false}
                size="small"
                scroll={{ y: 240 }}
              />
            </Card>
          </Col>
        </Row>

        {/* 指标概览 */}
        <Row gutter={16} className={styles.metricsRow}>
          {stats?.metrics_overview?.map((metric, index) => (
            <Col xs={24} sm={12} lg={8} key={index}>
              <Card size="small">
                <Statistic
                  title={metric.name}
                  value={metric.value}
                  precision={2}
                  valueStyle={{
                    color: metric.trend > 0 ? '#cf1322' : '#3f8600',
                  }}
                  suffix={metric.trend > 0 ? '↑' : '↓'}
                />
              </Card>
            </Col>
          ))}
        </Row>
      </div>
    </Spin>
  )
}

export default DashboardPage

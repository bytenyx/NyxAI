import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Card,
  Descriptions,
  Tag,
  Badge,
  Button,
  Space,
  Timeline,
  message,
  Spin,
  Row,
  Col,
  Divider,
} from 'antd'
import {
  ArrowLeftOutlined,
  CheckOutlined,
  CloseOutlined,
  PlayCircleOutlined,
} from '@ant-design/icons'
import { anomalyApi, rcaApi, recoveryApi } from '@services/api'
import { Anomaly, RCAResult, RecoveryStrategy } from '@types/index'
import dayjs from 'dayjs'
import styles from './Detail.module.css'

const severityColors = {
  critical: 'red',
  high: 'orange',
  medium: 'gold',
  low: 'green',
}

const severityLabels = {
  critical: '严重',
  high: '高',
  medium: '中',
  low: '低',
}

const AnomalyDetailPage = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [anomaly, setAnomaly] = useState<Anomaly | null>(null)
  const [rcaResult, setRcaResult] = useState<RCAResult | null>(null)
  const [strategies, setStrategies] = useState<RecoveryStrategy[]>([])
  const [loading, setLoading] = useState(true)

  const fetchData = async () => {
    if (!id) return
    setLoading(true)
    try {
      const [anomalyRes, strategiesRes] = await Promise.all([
        anomalyApi.getById(id),
        recoveryApi.getStrategies(),
      ])
      setAnomaly(anomalyRes.data)
      setStrategies(strategiesRes.data)

      // 获取 RCA 结果
      try {
        const rcaRes = await rcaApi.getResult(id)
        setRcaResult(rcaRes.data)
      } catch {
        // RCA 可能不存在
      }
    } catch (error) {
      message.error('获取异常详情失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [id])

  const handleAcknowledge = async () => {
    if (!id) return
    try {
      await anomalyApi.acknowledge(id)
      message.success('已确认异常')
      fetchData()
    } catch (error) {
      message.error('操作失败')
    }
  }

  const handleResolve = async () => {
    if (!id) return
    try {
      await anomalyApi.resolve(id)
      message.success('已解决异常')
      fetchData()
    } catch (error) {
      message.error('操作失败')
    }
  }

  const handleIgnore = async () => {
    if (!id) return
    try {
      await anomalyApi.ignore(id)
      message.success('已忽略异常')
      fetchData()
    } catch (error) {
      message.error('操作失败')
    }
  }

  const handleTriggerRCA = async () => {
    if (!id) return
    try {
      const res = await rcaApi.triggerAnalysis(id)
      setRcaResult(res.data)
      message.success('根因分析已触发')
    } catch (error) {
      message.error('触发分析失败')
    }
  }

  const handleExecuteRecovery = async (strategyId: string) => {
    if (!id) return
    try {
      await recoveryApi.execute(id, strategyId)
      message.success('恢复操作已执行')
    } catch (error) {
      message.error('执行失败')
    }
  }

  if (loading) {
    return (
      <div className={styles.loading}>
        <Spin size="large" />
      </div>
    )
  }

  if (!anomaly) {
    return <Card>异常不存在</Card>
  }

  const statusMap: Record<string, { color: string; text: string }> = {
    open: { color: 'red', text: '未处理' },
    acknowledged: { color: 'orange', text: '已确认' },
    resolved: { color: 'green', text: '已解决' },
    ignored: { color: 'default', text: '已忽略' },
  }

  const { color, text } = statusMap[anomaly.status] || { color: 'default', text: anomaly.status }

  return (
    <div className={styles.container}>
      <Card
        title={
          <Space>
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/anomalies')}>
              返回
            </Button>
            <span>异常详情</span>
          </Space>
        }
        extra={
          <Space>
            {anomaly.status === 'open' && (
              <Button icon={<CheckOutlined />} onClick={handleAcknowledge}>
                确认
              </Button>
            )}
            {(anomaly.status === 'open' || anomaly.status === 'acknowledged') && (
              <>
                <Button type="primary" icon={<CheckOutlined />} onClick={handleResolve}>
                  解决
                </Button>
                <Button danger icon={<CloseOutlined />} onClick={handleIgnore}>
                  忽略
                </Button>
              </>
            )}
          </Space>
        }
      >
        <Row gutter={24}>
          <Col span={16}>
            <Descriptions bordered column={2}>
              <Descriptions.Item label="异常标题">{anomaly.title}</Descriptions.Item>
              <Descriptions.Item label="服务">{anomaly.service}</Descriptions.Item>
              <Descriptions.Item label="指标">{anomaly.metric}</Descriptions.Item>
              <Descriptions.Item label="严重程度">
                <Tag color={severityColors[anomaly.severity]}>
                  {severityLabels[anomaly.severity]}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="当前值">{anomaly.value.toFixed(2)}</Descriptions.Item>
              <Descriptions.Item label="期望值">{anomaly.expectedValue.toFixed(2)}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Badge color={color} text={text} />
              </Descriptions.Item>
              <Descriptions.Item label="检测时间">
                {dayjs(anomaly.detectedAt).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
              {anomaly.resolvedAt && (
                <Descriptions.Item label="解决时间">
                  {dayjs(anomaly.resolvedAt).format('YYYY-MM-DD HH:mm:ss')}
                </Descriptions.Item>
              )}
              {anomaly.acknowledgedBy && (
                <Descriptions.Item label="确认人">{anomaly.acknowledgedBy}</Descriptions.Item>
              )}
            </Descriptions>

            <Divider orientation="left">异常描述</Divider>
            <p>{anomaly.description}</p>

            <Divider orientation="left">根因分析</Divider>
            {rcaResult ? (
              <div>
                <p>
                  <strong>根因:</strong> {rcaResult.rootCause}
                </p>
                <p>
                  <strong>置信度:</strong> {(rcaResult.confidence * 100).toFixed(1)}%
                </p>
                {rcaResult.llmAnalysis && (
                  <Card size="small" title="LLM 分析">
                    <pre className={styles.pre}>{rcaResult.llmAnalysis}</pre>
                  </Card>
                )}
              </div>
            ) : (
              <Space direction="vertical">
                <p>尚未进行根因分析</p>
                <Button type="primary" onClick={handleTriggerRCA}>
                  触发分析
                </Button>
              </Space>
            )}
          </Col>

          <Col span={8}>
            <Card title="恢复策略" size="small">
              {strategies.map((strategy) => (
                <div key={strategy.id} className={styles.strategyItem}>
                  <div className={styles.strategyInfo}>
                    <strong>{strategy.name}</strong>
                    <p>{strategy.description}</p>
                    <Tag color={strategy.riskLevel === 'L1' ? 'green' : strategy.riskLevel === 'L2' ? 'blue' : 'red'}>
                      {strategy.riskLevel}
                    </Tag>
                  </div>
                  <Button
                    type="primary"
                    size="small"
                    icon={<PlayCircleOutlined />}
                    onClick={() => handleExecuteRecovery(strategy.id)}
                    disabled={anomaly.status === 'resolved' || anomaly.status === 'ignored'}
                  >
                    执行
                  </Button>
                </div>
              ))}
            </Card>

            <Card title="事件时间线" size="small" style={{ marginTop: 16 }}>
              <Timeline
                items={[
                  {
                    children: `异常检测: ${dayjs(anomaly.detectedAt).format('HH:mm:ss')}`,
                    color: 'red',
                  },
                  ...(anomaly.acknowledgedAt
                    ? [
                        {
                          children: `确认: ${dayjs(anomaly.acknowledgedAt).format('HH:mm:ss')}`,
                          color: 'blue',
                        },
                      ]
                    : []),
                  ...(anomaly.resolvedAt
                    ? [
                        {
                          children: `解决: ${dayjs(anomaly.resolvedAt).format('HH:mm:ss')}`,
                          color: 'green',
                        },
                      ]
                    : []),
                  ...(rcaResult
                    ? [
                        {
                          children: `根因分析: ${dayjs(rcaResult.createdAt).format('HH:mm:ss')}`,
                          color: 'orange',
                        },
                      ]
                    : []),
                ]}
              />
            </Card>
          </Col>
        </Row>
      </Card>
    </div>
  )
}

export default AnomalyDetailPage

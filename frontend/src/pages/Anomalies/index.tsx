import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Table,
  Card,
  Tag,
  Badge,
  Button,
  Space,
  Select,
  Input,
  message,
  Popconfirm,
  Spin,
} from 'antd'
import {
  EyeOutlined,
  CheckOutlined,
  CloseOutlined,
  SearchOutlined,
} from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { anomalyApi } from '@services/api'
import { wsService } from '@services/websocket'
import { Anomaly, AnomalySeverity, AnomalyStatus, PaginationData } from '@types/index'
import dayjs from 'dayjs'
import styles from './styles.module.css'

const { Option } = Select

const AnomaliesPage = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [data, setData] = useState<PaginationData<Anomaly> | null>(null)
  const [loading, setLoading] = useState(false)
  const [filters, setFilters] = useState({
    severity: undefined as AnomalySeverity | undefined,
    status: undefined as AnomalyStatus | undefined,
    service: '',
  })
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
  })

  const severityColors: Record<AnomalySeverity, string> = {
    critical: 'red',
    high: 'orange',
    medium: 'gold',
    low: 'green',
  }

  const fetchData = async () => {
    setLoading(true)
    try {
      const response = await anomalyApi.getList({
        page: pagination.current,
        pageSize: pagination.pageSize,
        ...filters,
      })
      setData(response.data)
    } catch (error) {
      message.error(t('errors.fetchFailed'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()

    // 订阅实时更新
    const unsubscribe = wsService.subscribe('anomaly_detected', () => {
      fetchData()
    })

    return () => {
      unsubscribe()
    }
  }, [pagination.current, pagination.pageSize, filters])

  const handleAcknowledge = async (id: string) => {
    try {
      await anomalyApi.acknowledge(id)
      message.success(t('anomaly.actions.acknowledgeSuccess'))
      fetchData()
    } catch (error) {
      message.error(t('errors.operationFailed'))
    }
  }

  const handleResolve = async (id: string) => {
    try {
      await anomalyApi.resolve(id)
      message.success(t('anomaly.actions.resolveSuccess'))
      fetchData()
    } catch (error) {
      message.error(t('errors.operationFailed'))
    }
  }

  const handleIgnore = async (id: string) => {
    try {
      await anomalyApi.ignore(id)
      message.success(t('anomaly.actions.ignoreSuccess'))
      fetchData()
    } catch (error) {
      message.error(t('errors.operationFailed'))
    }
  }

  const columns = [
    {
      title: t('anomaly.fields.title'),
      dataIndex: 'title',
      key: 'title',
      render: (text: string, record: Anomaly) => (
        <a onClick={() => navigate(`/anomalies/${record.id}`)}>{text}</a>
      ),
    },
    {
      title: t('anomaly.fields.service'),
      dataIndex: 'service',
      key: 'service',
    },
    {
      title: t('anomaly.fields.metric'),
      dataIndex: 'metric',
      key: 'metric',
    },
    {
      title: t('anomaly.fields.currentValue'),
      dataIndex: 'value',
      key: 'value',
      render: (value: number, record: Anomaly) => (
        <span>
          {value.toFixed(2)} / {record.expectedValue.toFixed(2)}
        </span>
      ),
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
      render: (status: AnomalyStatus) => {
        const statusColors: Record<string, string> = {
          open: 'red',
          acknowledged: 'orange',
          resolved: 'green',
          ignored: 'default',
        }
        return <Badge color={statusColors[status]} text={t(`anomaly.status.${status}`)} />
      },
    },
    {
      title: t('anomaly.fields.detectedAt'),
      dataIndex: 'detectedAt',
      key: 'detectedAt',
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: t('common.action'),
      key: 'action',
      render: (_: unknown, record: Anomaly) => (
        <Space size="small">
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/anomalies/${record.id}`)}
          />
          {record.status === 'open' && (
            <Button
              type="text"
              icon={<CheckOutlined />}
              onClick={() => handleAcknowledge(record.id)}
              title={t('anomaly.actions.acknowledge')}
            />
          )}
          {(record.status === 'open' || record.status === 'acknowledged') && (
            <>
              <Popconfirm
                title={t('anomaly.actions.confirmResolve')}
                description={t('common.confirm')}
                onConfirm={() => handleResolve(record.id)}
                okText={t('common.confirm')}
                cancelText={t('common.cancel')}
              >
                <Button type="text" icon={<CheckOutlined />} title={t('anomaly.actions.resolve')} />
              </Popconfirm>
              <Popconfirm
                title={t('anomaly.actions.confirmIgnore')}
                description={t('common.confirm')}
                onConfirm={() => handleIgnore(record.id)}
                okText={t('common.confirm')}
                cancelText={t('common.cancel')}
              >
                <Button type="text" icon={<CloseOutlined />} title={t('anomaly.actions.ignore')} />
              </Popconfirm>
            </>
          )}
        </Space>
      ),
    },
  ]

  return (
    <Card
      title={t('anomaly.title')}
      extra={
        <Space>
          <Select
            placeholder={t('anomaly.fields.severity')}
            allowClear
            style={{ width: 120 }}
            value={filters.severity}
            onChange={(value) => setFilters({ ...filters, severity: value })}
          >
            <Option value="critical">{t('anomaly.severity.critical')}</Option>
            <Option value="high">{t('anomaly.severity.high')}</Option>
            <Option value="medium">{t('anomaly.severity.medium')}</Option>
            <Option value="low">{t('anomaly.severity.low')}</Option>
          </Select>
          <Select
            placeholder={t('anomaly.fields.status')}
            allowClear
            style={{ width: 120 }}
            value={filters.status}
            onChange={(value) => setFilters({ ...filters, status: value })}
          >
            <Option value="open">{t('anomaly.status.open')}</Option>
            <Option value="acknowledged">{t('anomaly.status.acknowledged')}</Option>
            <Option value="resolved">{t('anomaly.status.resolved')}</Option>
            <Option value="ignored">{t('anomaly.status.ignored')}</Option>
          </Select>
          <Input
            placeholder={t('anomaly.fields.service')}
            value={filters.service}
            onChange={(e) => setFilters({ ...filters, service: e.target.value })}
            style={{ width: 150 }}
            prefix={<SearchOutlined />}
          />
          <Button type="primary" onClick={fetchData}>
            {t('common.search')}
          </Button>
        </Space>
      }
    >
      <Spin spinning={loading}>
        <Table
          columns={columns}
          dataSource={data?.list || []}
          rowKey="id"
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: data?.total || 0,
            showSizeChanger: true,
            showTotal: (total) => `${t('common.all')} ${total} ${t('common.info')}`,
            onChange: (page, pageSize) => {
              setPagination({ current: page, pageSize: pageSize || 10 })
            },
          }}
        />
      </Spin>
    </Card>
  )
}

export default AnomaliesPage

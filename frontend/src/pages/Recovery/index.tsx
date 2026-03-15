import { useEffect, useState } from 'react'
import {
  Card,
  Table,
  Tag,
  Button,
  Space,
  message,
  Spin,
  Drawer,
  Descriptions,
  Timeline,
  Progress,
  Popconfirm,
} from 'antd'
import {
  PlayCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  EyeOutlined,
  ReloadOutlined,
  MedicineBoxOutlined,
} from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { recoveryApi } from '@services/api'
import { RecoveryAction, RecoveryStrategy, PaginationData, RecoveryStatus, RiskLevel } from '@types/index'
import dayjs from 'dayjs'
import styles from './styles.module.css'

const statusColors: Record<RecoveryStatus, string> = {
  pending: 'default',
  running: 'processing',
  completed: 'success',
  failed: 'error',
  cancelled: 'warning',
}

const riskLevelColors: Record<RiskLevel, string> = {
  L1: 'green',
  L2: 'blue',
  L3: 'orange',
  L4: 'red',
}

const RecoveryPage = () => {
  const { t } = useTranslation()
  const [actions, setActions] = useState<PaginationData<RecoveryAction> | null>(null)
  const [strategies, setStrategies] = useState<RecoveryStrategy[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedAction, setSelectedAction] = useState<RecoveryAction | null>(null)
  const [drawerVisible, setDrawerVisible] = useState(false)
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
  })

  const fetchData = async () => {
    setLoading(true)
    try {
      setActions({
        list: mockActions,
        total: mockActions.length,
        page: pagination.current,
        pageSize: pagination.pageSize,
      })
      setStrategies(mockStrategies)
    } catch (error) {
      message.error(t('errors.fetchFailed'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [pagination.current, pagination.pageSize])

  const handleViewDetail = (action: RecoveryAction) => {
    setSelectedAction(action)
    setDrawerVisible(true)
  }

  const handleApprove = async (actionId: string) => {
    try {
      await recoveryApi.approve(actionId)
      message.success(t('recovery.actions.approveSuccess'))
      fetchData()
    } catch (error) {
      message.error(t('errors.operationFailed'))
    }
  }

  const handleCancel = async (actionId: string) => {
    try {
      await recoveryApi.cancel(actionId)
      message.success(t('recovery.actions.cancelSuccess'))
      fetchData()
    } catch (error) {
      message.error(t('errors.operationFailed'))
    }
  }

  const actionColumns = [
    {
      title: t('recovery.fields.id'),
      dataIndex: 'id',
      key: 'id',
      ellipsis: true,
    },
    {
      title: t('recovery.fields.anomalyId'),
      dataIndex: 'anomalyId',
      key: 'anomalyId',
      ellipsis: true,
    },
    {
      title: t('recovery.fields.strategy'),
      dataIndex: 'strategyName',
      key: 'strategyName',
    },
    {
      title: t('recovery.fields.status'),
      dataIndex: 'status',
      key: 'status',
      render: (status: RecoveryStatus) => (
        <Tag color={statusColors[status]}>{t(`recovery.status.${status}`)}</Tag>
      ),
    },
    {
      title: t('recovery.fields.executedBy'),
      dataIndex: 'executedBy',
      key: 'executedBy',
      render: (user: string) => user || '-',
    },
    {
      title: t('recovery.fields.executedAt'),
      dataIndex: 'executedAt',
      key: 'executedAt',
      render: (time: string) => (time ? dayjs(time).format('MM-DD HH:mm') : '-'),
    },
    {
      title: t('common.action'),
      key: 'action',
      render: (_: unknown, record: RecoveryAction) => (
        <Space size="small">
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record)}
          >
            {t('common.view')}
          </Button>
          {record.status === 'pending' && (
            <Popconfirm
              title={t('recovery.actions.confirmApprove')}
              description={t('common.confirm')}
              onConfirm={() => handleApprove(record.id)}
              okText={t('common.confirm')}
              cancelText={t('common.cancel')}
            >
              <Button type="text" icon={<CheckCircleOutlined />}>
                {t('recovery.actions.approve')}
              </Button>
            </Popconfirm>
          )}
          {(record.status === 'pending' || record.status === 'running') && (
            <Popconfirm
              title={t('recovery.actions.confirmCancel')}
              description={t('common.confirm')}
              onConfirm={() => handleCancel(record.id)}
              okText={t('common.confirm')}
              cancelText={t('common.cancel')}
            >
              <Button type="text" danger icon={<CloseCircleOutlined />}>
                {t('recovery.actions.cancel')}
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ]

  const strategyColumns = [
    {
      title: t('recovery.fields.strategy'),
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: t('common.info'),
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: t('common.status'),
      dataIndex: 'type',
      key: 'type',
    },
    {
      title: t('recovery.fields.status'),
      dataIndex: 'riskLevel',
      key: 'riskLevel',
      render: (level: RiskLevel) => (
        <Tag color={riskLevelColors[level]}>{t(`recovery.riskLevel.${level}`)}</Tag>
      ),
    },
  ]

  // 模拟数据
  const mockActions: RecoveryAction[] = [
    {
      id: 'action-001',
      anomalyId: 'anomaly-001',
      strategyId: 'strategy-001',
      strategyName: '重启服务',
      status: 'completed',
      params: { service: 'user-service' },
      result: '服务重启成功，异常已恢复',
      executedBy: 'admin',
      executedAt: '2024-03-15T10:35:00Z',
      completedAt: '2024-03-15T10:36:30Z',
    },
    {
      id: 'action-002',
      anomalyId: 'anomaly-002',
      strategyId: 'strategy-002',
      strategyName: '扩容实例',
      status: 'running',
      params: { service: 'api-gateway', replicas: 5 },
      executedBy: 'admin',
      executedAt: '2024-03-15T11:00:00Z',
    },
    {
      id: 'action-003',
      anomalyId: 'anomaly-003',
      strategyId: 'strategy-003',
      strategyName: '清理缓存',
      status: 'pending',
      params: { cache: 'redis' },
    },
  ]

  const mockStrategies: RecoveryStrategy[] = [
    {
      id: 'strategy-001',
      name: '重启服务',
      description: '重启指定的服务实例',
      type: 'restart',
      riskLevel: 'L1',
      parameters: { service: 'string' },
    },
    {
      id: 'strategy-002',
      name: '扩容实例',
      description: '增加服务实例数量',
      type: 'scale',
      riskLevel: 'L2',
      parameters: { service: 'string', replicas: 'number' },
    },
    {
      id: 'strategy-003',
      name: '清理缓存',
      description: '清理 Redis 缓存',
      type: 'cache',
      riskLevel: 'L1',
      parameters: { cache: 'string' },
    },
    {
      id: 'strategy-004',
      name: '熔断降级',
      description: '启用熔断器，降级服务',
      type: 'circuit_breaker',
      riskLevel: 'L3',
      parameters: { service: 'string', threshold: 'number' },
    },
  ]

  return (
    <div className={styles.container}>
      <Card
        title={
          <Space>
            <MedicineBoxOutlined />
            <span>{t('recovery.title')}</span>
          </Space>
        }
        extra={
          <Button icon={<ReloadOutlined />} onClick={fetchData}>
            {t('common.refresh')}
          </Button>
        }
        className={styles.actionCard}
      >
        <Spin spinning={loading}>
          <Table
            columns={actionColumns}
            dataSource={mockActions}
            rowKey="id"
            pagination={{
              current: pagination.current,
              pageSize: pagination.pageSize,
              total: mockActions.length,
              showSizeChanger: true,
              showTotal: (total) => `${t('common.all')} ${total} ${t('common.info')}`,
              onChange: (page, pageSize) => {
                setPagination({ current: page, pageSize: pageSize || 10 })
              },
            }}
          />
        </Spin>
      </Card>

      <Card title={t('recovery.strategies')} className={styles.strategyCard}>
        <Table
          columns={strategyColumns}
          dataSource={mockStrategies}
          rowKey="id"
          pagination={false}
          size="small"
        />
      </Card>

      <Drawer
        title={t('recovery.detail')}
        width={600}
        open={drawerVisible}
        onClose={() => setDrawerVisible(false)}
      >
        {selectedAction && (
          <div>
            <Descriptions bordered column={1}>
              <Descriptions.Item label={t('recovery.fields.id')}>{selectedAction.id}</Descriptions.Item>
              <Descriptions.Item label={t('recovery.fields.anomalyId')}>{selectedAction.anomalyId}</Descriptions.Item>
              <Descriptions.Item label={t('recovery.fields.strategy')}>{selectedAction.strategyName}</Descriptions.Item>
              <Descriptions.Item label={t('recovery.fields.status')}>
                <Tag color={statusColors[selectedAction.status]}>
                  {t(`recovery.status.${selectedAction.status}`)}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label={t('recovery.fields.params')}>
                <pre className={styles.code}>
                  {JSON.stringify(selectedAction.params, null, 2)}
                </pre>
              </Descriptions.Item>
              {selectedAction.result && (
                <Descriptions.Item label={t('recovery.fields.result')}>{selectedAction.result}</Descriptions.Item>
              )}
              {selectedAction.error && (
                <Descriptions.Item label={t('recovery.fields.error')}>
                  <span style={{ color: 'red' }}>{selectedAction.error}</span>
                </Descriptions.Item>
              )}
              {selectedAction.executedBy && (
                <Descriptions.Item label={t('recovery.fields.executedBy')}>{selectedAction.executedBy}</Descriptions.Item>
              )}
              {selectedAction.executedAt && (
                <Descriptions.Item label={t('recovery.fields.executedAt')}>
                  {dayjs(selectedAction.executedAt).format('YYYY-MM-DD HH:mm:ss')}
                </Descriptions.Item>
              )}
              {selectedAction.completedAt && (
                <Descriptions.Item label={t('recovery.fields.completedAt')}>
                  {dayjs(selectedAction.completedAt).format('YYYY-MM-DD HH:mm:ss')}
                </Descriptions.Item>
              )}
              {selectedAction.approvedBy && (
                <Descriptions.Item label={t('recovery.fields.approvedBy')}>{selectedAction.approvedBy}</Descriptions.Item>
              )}
            </Descriptions>

            {selectedAction.status === 'running' && (
              <div style={{ marginTop: 16 }}>
                <Progress percent={60} status="active" />
              </div>
            )}

            <Card title={t('recovery.logs')} size="small" style={{ marginTop: 16 }}>
              <Timeline
                items={[
                  {
                    children: `${t('recovery.logs')}: ${dayjs(selectedAction.executedAt || Date.now()).format('HH:mm:ss')}`,
                    color: 'blue',
                  },
                  ...(selectedAction.approvedAt
                    ? [
                        {
                          children: `${t('recovery.actions.approve')}: ${dayjs(selectedAction.approvedAt).format('HH:mm:ss')}`,
                          color: 'green',
                        },
                      ]
                    : []),
                  ...(selectedAction.executedAt
                    ? [
                        {
                          children: `${t('recovery.actions.execute')}: ${dayjs(selectedAction.executedAt).format('HH:mm:ss')}`,
                          color: 'orange',
                        },
                      ]
                    : []),
                  ...(selectedAction.completedAt
                    ? [
                        {
                          children: `${t('recovery.status.completed')}: ${dayjs(selectedAction.completedAt).format('HH:mm:ss')}`,
                          color: 'green',
                        },
                      ]
                    : []),
                ]}
              />
            </Card>
          </div>
        )}
      </Drawer>
    </div>
  )
}

export default RecoveryPage

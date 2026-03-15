import { useState } from 'react'
import {
  Card,
  Table,
  Tag,
  Button,
  Space,
  Input,
  message,
  Spin,
  Drawer,
  Descriptions,
  Timeline,
} from 'antd'
import {
  EyeOutlined,
  SearchOutlined,
  ReloadOutlined,
  NodeIndexOutlined,
} from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { rcaApi } from '@services/api'
import { RCAResult, PaginationData } from '@types/index'
import dayjs from 'dayjs'
import styles from './styles.module.css'

const RCAPage = () => {
  const { t } = useTranslation()
  const [data, setData] = useState<PaginationData<RCAResult> | null>(null)
  const [loading, setLoading] = useState(false)
  const [selectedRCA, setSelectedRCA] = useState<RCAResult | null>(null)
  const [drawerVisible, setDrawerVisible] = useState(false)
  const [filters, setFilters] = useState({
    anomalyId: '',
  })
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
  })

  const fetchData = async () => {
    setLoading(true)
    try {
      setData({
        list: mockData,
        total: mockData.length,
        page: pagination.current,
        pageSize: pagination.pageSize,
      })
    } catch (error) {
      message.error(t('errors.fetchFailed'))
    } finally {
      setLoading(false)
    }
  }

  const handleViewDetail = async (rca: RCAResult) => {
    setSelectedRCA(rca)
    setDrawerVisible(true)
  }

  const handleTriggerRCA = async (anomalyId: string) => {
    try {
      const res = await rcaApi.triggerAnalysis(anomalyId)
      message.success(t('rca.triggerSuccess'))
      fetchData()
    } catch (error) {
      message.error(t('rca.triggerError'))
    }
  }

  const columns = [
    {
      title: t('rca.fields.id'),
      dataIndex: 'id',
      key: 'id',
      ellipsis: true,
    },
    {
      title: t('rca.fields.anomalyId'),
      dataIndex: 'anomalyId',
      key: 'anomalyId',
      ellipsis: true,
    },
    {
      title: t('rca.fields.rootCause'),
      dataIndex: 'rootCause',
      key: 'rootCause',
      ellipsis: true,
    },
    {
      title: t('rca.fields.confidence'),
      dataIndex: 'confidence',
      key: 'confidence',
      render: (confidence: number) => (
        <Tag color={confidence > 0.8 ? 'green' : confidence > 0.5 ? 'orange' : 'red'}>
          {(confidence * 100).toFixed(1)}%
        </Tag>
      ),
    },
    {
      title: t('rca.fields.createdAt'),
      dataIndex: 'createdAt',
      key: 'createdAt',
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: t('common.action'),
      key: 'action',
      render: (_: unknown, record: RCAResult) => (
        <Space size="small">
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record)}
          >
            {t('common.view')}
          </Button>
        </Space>
      ),
    },
  ]

  // 模拟 RCA 数据
  const mockData: RCAResult[] = [
    {
      id: 'rca-001',
      anomalyId: 'anomaly-001',
      rootCause: '数据库连接池耗尽导致服务响应超时',
      confidence: 0.92,
      createdAt: '2024-03-15T10:30:00Z',
      serviceGraph: {
        nodes: [
          { id: 'api-gateway', name: 'API Gateway', status: 'warning', metrics: { latency: 500, errorRate: 0.05 } },
          { id: 'user-service', name: 'User Service', status: 'error', metrics: { latency: 2000, errorRate: 0.3 } },
          { id: 'database', name: 'Database', status: 'critical', metrics: { latency: 5000, errorRate: 0.8 } },
        ],
        edges: [
          { source: 'api-gateway', target: 'user-service', latency: 100, errorRate: 0.01 },
          { source: 'user-service', target: 'database', latency: 200, errorRate: 0.05 },
        ],
      },
      dimensionAttribution: [
        { dimension: 'region', value: 'us-east-1', contribution: 0.6, isAnomalous: true },
        { dimension: 'version', value: 'v2.1.0', contribution: 0.3, isAnomalous: false },
        { dimension: 'instance', value: 'i-123456', contribution: 0.1, isAnomalous: false },
      ],
      llmAnalysis: `根据分析，本次异常的主要根因是数据库连接池配置不当导致连接耗尽。

**故障传播路径：**
1. 数据库连接池达到最大连接数限制
2. User Service 无法获取数据库连接，导致请求堆积
3. API Gateway 检测到 User Service 响应超时
4. 最终用户请求失败

**建议措施：**
1. 增加数据库连接池大小
2. 优化慢查询语句
3. 增加连接池监控告警`,
    },
  ]

  return (
    <Card
      title={
        <Space>
          <NodeIndexOutlined />
          <span>{t('rca.title')}</span>
        </Space>
      }
      extra={
        <Space>
          <Input
            placeholder={t('rca.fields.anomalyId')}
            value={filters.anomalyId}
            onChange={(e) => setFilters({ ...filters, anomalyId: e.target.value })}
            style={{ width: 200 }}
            prefix={<SearchOutlined />}
          />
          <Button type="primary" onClick={fetchData}>
            {t('common.search')}
          </Button>
          <Button icon={<ReloadOutlined />} onClick={fetchData}>
            {t('common.refresh')}
          </Button>
        </Space>
      }
    >
      <Spin spinning={loading}>
        <Table
          columns={columns}
          dataSource={mockData}
          rowKey="id"
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: mockData.length,
            showSizeChanger: true,
            showTotal: (total) => `${t('common.all')} ${total} ${t('common.info')}`,
            onChange: (page, pageSize) => {
              setPagination({ current: page, pageSize: pageSize || 10 })
            },
          }}
        />
      </Spin>

      <Drawer
        title={t('rca.detail')}
        width={800}
        open={drawerVisible}
        onClose={() => setDrawerVisible(false)}
      >
        {selectedRCA && (
          <div>
            <Descriptions bordered column={1}>
              <Descriptions.Item label={t('rca.fields.id')}>{selectedRCA.id}</Descriptions.Item>
              <Descriptions.Item label={t('rca.fields.anomalyId')}>{selectedRCA.anomalyId}</Descriptions.Item>
              <Descriptions.Item label={t('rca.fields.rootCause')}>{selectedRCA.rootCause}</Descriptions.Item>
              <Descriptions.Item label={t('rca.fields.confidence')}>
                <Tag color={selectedRCA.confidence > 0.8 ? 'green' : selectedRCA.confidence > 0.5 ? 'orange' : 'red'}>
                  {(selectedRCA.confidence * 100).toFixed(1)}%
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label={t('rca.fields.createdAt')}>
                {dayjs(selectedRCA.createdAt).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
            </Descriptions>

            {selectedRCA.serviceGraph && (
              <Card title={t('rca.serviceGraph')} size="small" style={{ marginTop: 16 }}>
                <div className={styles.serviceGraph}>
                  {selectedRCA.serviceGraph.nodes.map((node) => (
                    <div
                      key={node.id}
                      className={styles.serviceNode}
                      style={{
                        borderColor:
                          node.status === 'normal'
                            ? '#52c41a'
                            : node.status === 'warning'
                            ? '#faad14'
                            : node.status === 'error'
                            ? '#f5222d'
                            : '#722ed1',
                      }}
                    >
                      <strong>{node.name}</strong>
                      <div className={styles.nodeMetrics}>
                        <span>{t('rca.nodes.latency')}: {node.metrics.latency}ms</span>
                        <span>{t('rca.nodes.errorRate')}: {(node.metrics.errorRate * 100).toFixed(1)}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {selectedRCA.dimensionAttribution && (
              <Card title={t('rca.dimensionAttribution')} size="small" style={{ marginTop: 16 }}>
                {selectedRCA.dimensionAttribution.map((dim) => (
                  <div key={dim.dimension} className={styles.dimensionItem}>
                    <div className={styles.dimensionHeader}>
                      <Tag color={dim.isAnomalous ? 'red' : 'default'}>{dim.dimension}</Tag>
                      <span>{dim.value}</span>
                    </div>
                    <div className={styles.contributionBar}>
                      <div
                        className={styles.contributionFill}
                        style={{
                          width: `${dim.contribution * 100}%`,
                          backgroundColor: dim.isAnomalous ? '#ff4d4f' : '#52c41a',
                        }}
                      />
                      <span>{(dim.contribution * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                ))}
              </Card>
            )}

            {selectedRCA.llmAnalysis && (
              <Card title={t('rca.fields.llmAnalysis')} size="small" style={{ marginTop: 16 }}>
                <pre className={styles.llmAnalysis}>{selectedRCA.llmAnalysis}</pre>
              </Card>
            )}
          </div>
        )}
      </Drawer>
    </Card>
  )
}

export default RCAPage

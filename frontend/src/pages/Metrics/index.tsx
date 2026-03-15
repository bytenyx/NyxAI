import { useState } from 'react'
import {
  Card,
  Form,
  Input,
  DatePicker,
  Button,
  Select,
  Space,
  message,
  Spin,
  Row,
  Col,
} from 'antd'
import { SearchOutlined, DownloadOutlined } from '@ant-design/icons'
import { Line } from '@ant-design/charts'
import { useTranslation } from 'react-i18next'
import { metricsApi } from '@services/api'
import { Metric, MetricQueryParams } from '@types/index'
import dayjs from 'dayjs'
import styles from './styles.module.css'

const { RangePicker } = DatePicker
const { Option } = Select

const MetricsPage = () => {
  const { t } = useTranslation()
  const [form] = Form.useForm()
  const [metrics, setMetrics] = useState<Metric[]>([])
  const [loading, setLoading] = useState(false)

  const handleQuery = async (values: { query: string; timeRange: [dayjs.Dayjs, dayjs.Dayjs]; step?: number }) => {
    if (!values.timeRange || values.timeRange.length !== 2) {
      message.error(t('metrics.query.timeRange'))
      return
    }

    setLoading(true)
    try {
      const params: MetricQueryParams = {
        query: values.query,
        start: values.timeRange[0].unix(),
        end: values.timeRange[1].unix(),
        step: values.step || 60,
      }
      const res = await metricsApi.query(params)
      setMetrics(res.data)
    } catch (error) {
      message.error(t('errors.fetchFailed'))
    } finally {
      setLoading(false)
    }
  }

  // 转换数据为图表格式
  const getChartData = () => {
    const data: { time: string; value: number; metric: string }[] = []
    metrics.forEach((metric) => {
      metric.values.forEach((v) => {
        data.push({
          time: dayjs(v.timestamp * 1000).format('HH:mm'),
          value: v.value,
          metric: metric.name,
        })
      })
    })
    return data
  }

  const chartConfig = {
    data: getChartData(),
    xField: 'time',
    yField: 'value',
    seriesField: 'metric',
    smooth: true,
    animation: {
      appear: {
        animation: 'path-in',
        duration: 1000,
      },
    },
    yAxis: {
      label: {
        formatter: (v: number) => `${v}`,
      },
    },
    legend: {
      position: 'top',
    },
  }

  const handleExport = () => {
    const data = getChartData()
    const csv = [
      ['Time', 'Metric', 'Value'].join(','),
      ...data.map((d) => [d.time, d.metric, d.value].join(',')),
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `metrics_${dayjs().format('YYYY-MM-DD_HH-mm')}.csv`
    link.click()
  }

  const quickQueries = [
    { name: t('metrics.queries.serviceStatus'), query: 'up' },
    { name: t('metrics.queries.cpuUsage'), query: '100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)' },
    { name: t('metrics.queries.memoryUsage'), query: '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100' },
    { name: t('metrics.queries.diskUsage'), query: '(1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100' },
    { name: t('metrics.queries.networkReceive'), query: 'rate(node_network_receive_bytes_total[5m])' },
    { name: t('metrics.queries.networkTransmit'), query: 'rate(node_network_transmit_bytes_total[5m])' },
  ]

  return (
    <div className={styles.container}>
      <Card title={t('metrics.query.title')}>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleQuery}
          initialValues={{
            query: 'up',
            step: 60,
          }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label={t('metrics.query.promql')}
                name="query"
                rules={[{ required: true, message: t('metrics.query.placeholder') }]}
              >
                <Input.TextArea
                  placeholder={t('metrics.query.placeholder')}
                  rows={2}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label={t('metrics.query.timeRange')}
                name="timeRange"
                rules={[{ required: true, message: t('metrics.query.timeRange') }]}
              >
                <RangePicker
                  showTime
                  format="YYYY-MM-DD HH:mm"
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item label={t('metrics.query.step')} name="step">
                <Select>
                  <Option value={15}>{t('metrics.step.15s')}</Option>
                  <Option value={30}>{t('metrics.step.30s')}</Option>
                  <Option value={60}>{t('metrics.step.1m')}</Option>
                  <Option value={300}>{t('metrics.step.5m')}</Option>
                  <Option value={900}>{t('metrics.step.15m')}</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={16}>
              <Form.Item label=" ">
                <Space>
                  <Button
                    type="primary"
                    htmlType="submit"
                    icon={<SearchOutlined />}
                    loading={loading}
                  >
                    {t('metrics.query.submit')}
                  </Button>
                  <Button icon={<DownloadOutlined />} onClick={handleExport} disabled={metrics.length === 0}>
                    {t('metrics.query.export')}
                  </Button>
                </Space>
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Card>

      <Card title={t('metrics.result')} className={styles.chartCard}>
        <Spin spinning={loading}>
          {metrics.length > 0 ? (
            <Line {...chartConfig} height={400} />
          ) : (
            <div className={styles.empty}>{t('metrics.query.placeholder')}</div>
          )}
        </Spin>
      </Card>

      <Card title={t('metrics.quickQueries')} size="small" className={styles.quickQueries}>
        <Space wrap>
          {quickQueries.map((item) => (
            <Button
              key={item.name}
              size="small"
              onClick={() => {
                form.setFieldsValue({ query: item.query })
              }}
            >
              {item.name}
            </Button>
          ))}
        </Space>
      </Card>
    </div>
  )
}

export default MetricsPage

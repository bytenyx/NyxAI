import React from 'react'
import { Form, Input, Select, Button, message } from 'antd'
import type { DataSource, DataSourceCreate, DataSourceUpdate } from '../../types/datasource'
import { datasourceApi } from '../../services/datasourceApi'
import { useSettingsStore } from '../../stores/settingsStore'

interface DataSourceFormProps {
  mode: 'add' | 'edit'
  data?: DataSource
  onSuccess: () => void
}

const DataSourceForm: React.FC<DataSourceFormProps> = ({
  mode,
  data,
  onSuccess,
}) => {
  const { setDatasources } = useSettingsStore()
  const [form] = Form.useForm()

  const handleSubmit = async (values: unknown) => {
    try {
      if (mode === 'add') {
        await datasourceApi.create(values as unknown as DataSourceCreate)
        message.success('添加成功')
      } else {
        await datasourceApi.update(data!.id, values as unknown as DataSourceUpdate)
        message.success('更新成功')
      }
      const updated = await datasourceApi.list()
      setDatasources(updated)
      onSuccess()
    } catch (error) {
      message.error('操作失败')
    }
  }

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={data || { auth_type: 'none' }}
      onFinish={handleSubmit}
    >
      <Form.Item name="type" label="数据源类型" rules={[{ required: true }]}>
        <Select disabled={mode === 'edit'}>
          <Select.Option value="prometheus">Prometheus</Select.Option>
          <Select.Option value="influxdb">InfluxDB</Select.Option>
          <Select.Option value="loki">Loki</Select.Option>
          <Select.Option value="jaeger">Jaeger</Select.Option>
        </Select>
      </Form.Item>

      <Form.Item name="name" label="名称" rules={[{ required: true }]}>
        <Input />
      </Form.Item>

      <Form.Item name="url" label="URL" rules={[{ required: true }]}>
        <Input />
      </Form.Item>

      <Form.Item name="auth_type" label="认证方式">
        <Select>
          <Select.Option value="none">无认证</Select.Option>
          <Select.Option value="basic">Basic Auth</Select.Option>
          <Select.Option value="bearer">Bearer Token</Select.Option>
          <Select.Option value="api_key">API Key</Select.Option>
        </Select>
      </Form.Item>

      <Form.Item>
        <Button type="primary" htmlType="submit" block>
          保存
        </Button>
      </Form.Item>
    </Form>
  )
}

export default DataSourceForm

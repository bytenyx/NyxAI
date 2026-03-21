import React from 'react'
import { List, Tag, Button, Space, message } from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ApiOutlined,
} from '@ant-design/icons'
import { useSettingsStore } from '../../stores/settingsStore'
import { datasourceApi } from '../../services/datasourceApi'
import type { DataSource } from '../../types/datasource'

const statusColors: Record<string, string> = {
  connected: 'success',
  disconnected: 'warning',
  error: 'error',
  not_configured: 'default',
}

const statusLabels: Record<string, string> = {
  connected: '已连接',
  disconnected: '已断开',
  error: '连接失败',
  not_configured: '未配置',
}

const DataSourceList: React.FC = () => {
  const { datasources, openSlidePanel, setDatasources } = useSettingsStore()

  const handleTest = async (ds: DataSource) => {
    try {
      const result = await datasourceApi.test(ds.id)
      if (result.success) {
        message.success(`连接成功 (${result.latency_ms}ms)`)
      } else {
        message.error(`连接失败: ${result.message}`)
      }
      const updated = await datasourceApi.list()
      setDatasources(updated)
    } catch (error) {
      message.error('测试失败')
    }
  }

  const handleDelete = async (ds: DataSource) => {
    try {
      await datasourceApi.delete(ds.id)
      const updated = await datasourceApi.list()
      setDatasources(updated)
      message.success('删除成功')
    } catch (error) {
      message.error('删除失败')
    }
  }

  return (
    <div className="datasource-list">
      <div className="datasource-header">
        <h3>数据源管理</h3>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => openSlidePanel('add', 'datasource')}
        >
          添加数据源
        </Button>
      </div>

      <List
        dataSource={datasources}
        renderItem={(ds) => (
          <List.Item
            actions={[
              <Button
                key="test"
                type="link"
                icon={<ApiOutlined />}
                onClick={() => handleTest(ds)}
              >
                测试
              </Button>,
              <Button
                key="edit"
                type="link"
                icon={<EditOutlined />}
                onClick={() => openSlidePanel('edit', 'datasource', ds)}
              >
                编辑
              </Button>,
              <Button
                key="delete"
                type="link"
                danger
                icon={<DeleteOutlined />}
                onClick={() => handleDelete(ds)}
              >
                删除
              </Button>,
            ]}
          >
            <List.Item.Meta
              title={
                <Space>
                  <span>{ds.name}</span>
                  <Tag color={statusColors[ds.status]}>{statusLabels[ds.status]}</Tag>
                </Space>
              }
              description={
                <div>
                  <div>{ds.url}</div>
                  {ds.error_message && (
                    <div style={{ color: '#ff4d4f' }}>{ds.error_message}</div>
                  )}
                </div>
              }
            />
          </List.Item>
        )}
      />
    </div>
  )
}

export default DataSourceList

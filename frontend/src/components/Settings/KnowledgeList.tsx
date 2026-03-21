import React, { useState } from 'react'
import {
  List,
  Tag,
  Button,
  Space,
  Input,
  Select,
  Upload,
  message,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  UploadOutlined,
  SearchOutlined,
} from '@ant-design/icons'
import { useSettingsStore } from '../../stores/settingsStore'
import { knowledgeApi } from '../../services/knowledgeApi'
import type { Knowledge } from '../../types/knowledge'

const KnowledgeList: React.FC = () => {
  const { knowledge, openSlidePanel, setKnowledge } = useSettingsStore()
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState<string>('all')

  const handleUpload = async (file: File) => {
    try {
      await knowledgeApi.upload(file)
      const updated = await knowledgeApi.list()
      setKnowledge(updated)
      message.success('上传成功')
    } catch (error) {
      message.error('上传失败')
    }
    return false
  }

  const handleDelete = async (item: Knowledge) => {
    try {
      await knowledgeApi.delete(item.id)
      const updated = await knowledgeApi.list()
      setKnowledge(updated)
      message.success('删除成功')
    } catch (error) {
      message.error('删除失败')
    }
  }

  const filtered = knowledge.filter((k) => {
    const matchSearch = k.title.toLowerCase().includes(search.toLowerCase())
    const matchType = typeFilter === 'all' || k.knowledge_type === typeFilter
    return matchSearch && matchType
  })

  return (
    <div className="knowledge-list">
      <div className="knowledge-toolbar">
        <Space>
          <Input
            placeholder="搜索知识..."
            prefix={<SearchOutlined />}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: 200 }}
          />
          <Select value={typeFilter} onChange={setTypeFilter} style={{ width: 120 }}>
            <Select.Option value="all">全部类型</Select.Option>
            <Select.Option value="text">文本</Select.Option>
            <Select.Option value="file">文件</Select.Option>
          </Select>
        </Space>
        <Space>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => openSlidePanel('add', 'knowledge')}
          >
            添加
          </Button>
          <Upload
            beforeUpload={handleUpload}
            showUploadList={false}
            accept=".pdf,.doc,.docx,.txt"
          >
            <Button icon={<UploadOutlined />}>上传</Button>
          </Upload>
        </Space>
      </div>

      <List
        dataSource={filtered}
        renderItem={(item) => (
          <List.Item
            actions={[
              <Button
                key="edit"
                type="link"
                icon={<EditOutlined />}
                onClick={() => openSlidePanel('edit', 'knowledge', item)}
              >
                编辑
              </Button>,
              <Button
                key="delete"
                type="link"
                danger
                icon={<DeleteOutlined />}
                onClick={() => handleDelete(item)}
              >
                删除
              </Button>,
            ]}
          >
            <List.Item.Meta
              title={
                <Space>
                  <span>{item.title}</span>
                  <Tag>{item.knowledge_type === 'text' ? '文本' : '文件'}</Tag>
                </Space>
              }
              description={
                <div>
                  <div>
                    标签:
                    {item.tags.map((t) => (
                      <Tag key={t}>{t}</Tag>
                    ))}
                  </div>
                  <div>
                    更新: {new Date(item.updated_at).toLocaleDateString()} | 引用:
                    {item.reference_count}次
                  </div>
                </div>
              }
            />
          </List.Item>
        )}
      />
    </div>
  )
}

export default KnowledgeList

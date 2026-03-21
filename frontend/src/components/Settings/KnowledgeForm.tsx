import React from 'react'
import { Form, Input, Select, Button, message } from 'antd'
import type { Knowledge, KnowledgeCreate, KnowledgeUpdate } from '../../types/knowledge'
import { knowledgeApi } from '../../services/knowledgeApi'
import { useSettingsStore } from '../../stores/settingsStore'

interface KnowledgeFormProps {
  mode: 'add' | 'edit'
  data?: Knowledge
  onSuccess: () => void
}

const KnowledgeForm: React.FC<KnowledgeFormProps> = ({
  mode,
  data,
  onSuccess,
}) => {
  const { setKnowledge, knowledgeTags } = useSettingsStore()
  const [form] = Form.useForm()

  const handleSubmit = async (values: unknown) => {
    try {
      if (mode === 'add') {
        await knowledgeApi.create(values as unknown as KnowledgeCreate)
        message.success('添加成功')
      } else {
        await knowledgeApi.update(data!.id, values as unknown as KnowledgeUpdate)
        message.success('更新成功')
      }
      const updated = await knowledgeApi.list()
      setKnowledge(updated)
      onSuccess()
    } catch (error) {
      message.error('操作失败')
    }
  }

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={data || { type: 'text', tags: [] }}
      onFinish={handleSubmit}
    >
      <Form.Item name="title" label="标题" rules={[{ required: true }]}>
        <Input />
      </Form.Item>

      <Form.Item name="type" label="类型">
        <Select>
          <Select.Option value="text">文本</Select.Option>
          <Select.Option value="file">文件</Select.Option>
        </Select>
      </Form.Item>

      <Form.Item name="content" label="内容">
        <Input.TextArea rows={6} />
      </Form.Item>

      <Form.Item name="tags" label="标签">
        <Select mode="tags" placeholder="输入标签">
          {knowledgeTags.map((tag) => (
            <Select.Option key={tag} value={tag}>
              {tag}
            </Select.Option>
          ))}
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

export default KnowledgeForm

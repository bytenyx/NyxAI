import React, { useEffect, useState } from 'react'
import { Form, Input, Select, Button, message, Card } from 'antd'
import type { AgentConfig, AgentConfigCreate, AgentConfigUpdate } from '../../types/agentConfig'
import { agentConfigApi } from '../../services/agentConfigApi'
import SkillSelector from './SkillSelector'

const { TextArea } = Input
const { Option } = Select

const AGENT_TYPES = [
  { value: 'investigation', label: '调查 Agent' },
  { value: 'diagnosis', label: '诊断 Agent' },
  { value: 'recovery', label: '恢复 Agent' },
  { value: 'orchestrator', label: '编排 Agent' },
]

interface ConfigEditorProps {
  config?: AgentConfig
  onSave: () => void
  onCancel: () => void
}

const ConfigEditor: React.FC<ConfigEditorProps> = ({ config, onSave, onCancel }) => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (config) {
      form.setFieldsValue(config)
    } else {
      form.resetFields()
    }
  }, [config, form])

  const handleSubmit = async (values: AgentConfigCreate | AgentConfigUpdate) => {
    setLoading(true)
    try {
      if (config) {
        await agentConfigApi.update(config.id, values)
        message.success('配置已更新')
      } else {
        await agentConfigApi.create(values as AgentConfigCreate)
        message.success('配置已创建')
      }
      onSave()
    } catch {
      message.error('保存失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={handleSubmit}
      initialValues={{ allowed_skills: [] }}
    >
      <Form.Item
        name="agent_type"
        label="Agent 类型"
        rules={[{ required: true, message: '请选择 Agent 类型' }]}
      >
        <Select disabled={!!config}>
          {AGENT_TYPES.map(t => (
            <Option key={t.value} value={t.value}>{t.label}</Option>
          ))}
        </Select>
      </Form.Item>

      <Form.Item
        name="name"
        label="配置名称"
        rules={[{ required: true, message: '请输入配置名称' }]}
      >
        <Input placeholder="如：默认诊断配置" />
      </Form.Item>

      <Form.Item
        name="system_prompt"
        label="系统提示词"
        rules={[{ required: true, message: '请输入系统提示词' }]}
      >
        <TextArea rows={10} placeholder="输入 Agent 的系统提示词..." />
      </Form.Item>

      <Form.Item
        name="allowed_skills"
        label="可用技能"
      >
        <SkillSelector />
      </Form.Item>

      <Form.Item
        name="change_reason"
        label="变更说明"
      >
        <Input placeholder="描述本次变更的原因（可选）" />
      </Form.Item>

      <Form.Item>
        <Button type="primary" htmlType="submit" loading={loading}>
          保存
        </Button>
        <Button style={{ marginLeft: 8 }} onClick={onCancel}>
          取消
        </Button>
      </Form.Item>
    </Form>
  )
}

export default ConfigEditor

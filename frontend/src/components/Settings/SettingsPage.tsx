import React, { useEffect, useState } from 'react'
import { Modal, Button, List, message } from 'antd'
import { useSettingsStore } from '../../stores/settingsStore'
import SettingsSidebar from './SettingsSidebar'
import DataSourceList from './DataSourceList'
import KnowledgeList from './KnowledgeList'
import SlidePanel from './SlidePanel'
import ConfigEditor from '../AgentConfig/ConfigEditor'
import { datasourceApi } from '../../services/datasourceApi'
import { knowledgeApi } from '../../services/knowledgeApi'
import { agentConfigApi } from '../../services/agentConfigApi'
import type { AgentConfig } from '../../types/agentConfig'

const SettingsPage: React.FC = () => {
  const {
    isOpen,
    closeSettings,
    activeTab,
    setDatasources,
    setKnowledge,
    setKnowledgeTags,
  } = useSettingsStore()

  const [configs, setConfigs] = useState<AgentConfig[]>([])
  const [editingConfig, setEditingConfig] = useState<AgentConfig | undefined>()
  const [showEditor, setShowEditor] = useState(false)

  useEffect(() => {
    if (isOpen) {
      loadData()
    }
  }, [isOpen])

  useEffect(() => {
    if (activeTab === 'agentConfig' && isOpen) {
      loadConfigs()
    }
  }, [activeTab, isOpen])

  const loadData = async () => {
    try {
      const [datasources, knowledge, tags] = await Promise.all([
        datasourceApi.list(),
        knowledgeApi.list(),
        knowledgeApi.getTags(),
      ])
      setDatasources(datasources)
      setKnowledge(knowledge)
      setKnowledgeTags(tags)
    } catch (error) {
      console.error('Failed to load settings data:', error)
    }
  }

  const loadConfigs = async () => {
    try {
      const configList = await agentConfigApi.list()
      setConfigs(configList)
    } catch (error) {
      console.error('Failed to load agent configs:', error)
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await agentConfigApi.delete(id)
      message.success('配置已删除')
      loadConfigs()
    } catch {
      message.error('删除失败')
    }
  }

  const handleActivate = async (id: string) => {
    try {
      await agentConfigApi.activate(id)
      message.success('配置已激活')
      loadConfigs()
    } catch {
      message.error('激活失败')
    }
  }

  const renderAgentConfigContent = () => (
    <div style={{ padding: '24px' }}>
      <Button
        type="primary"
        onClick={() => {
          setEditingConfig(undefined)
          setShowEditor(true)
        }}
        style={{ marginBottom: '16px' }}
      >
        新建配置
      </Button>
      <List
        dataSource={configs}
        renderItem={(item) => (
          <List.Item
            actions={[
              <Button
                key="edit"
                type="link"
                onClick={() => {
                  setEditingConfig(item)
                  setShowEditor(true)
                }}
              >
                编辑
              </Button>,
              <Button
                key="activate"
                type="link"
                onClick={() => handleActivate(item.id)}
                disabled={item.is_active}
              >
                {item.is_active ? '已激活' : '激活'}
              </Button>,
              <Button
                key="delete"
                type="link"
                danger
                onClick={() => handleDelete(item.id)}
              >
                删除
              </Button>,
            ]}
          >
            <List.Item.Meta
              title={`${item.name} ${item.is_active ? '(激活)' : ''}`}
              description={`类型: ${item.agent_type} | 技能: ${item.allowed_skills.join(', ') || '无'}`}
            />
          </List.Item>
        )}
      />
      {showEditor && (
        <Modal
          open={showEditor}
          onCancel={() => setShowEditor(false)}
          footer={null}
          width={800}
          title={editingConfig ? '编辑配置' : '新建配置'}
        >
          <ConfigEditor
            config={editingConfig}
            onSave={() => {
              setShowEditor(false)
              loadConfigs()
            }}
            onCancel={() => setShowEditor(false)}
          />
        </Modal>
      )}
    </div>
  )

  return (
    <>
      <Modal
        className="settings-modal"
        open={isOpen}
        onCancel={closeSettings}
        footer={null}
        width="100%"
        style={{ top: 0, maxWidth: '100vw' }}
        closable
        title="设置"
      >
        <div className="settings-page">
          <SettingsSidebar />
          <div className="settings-content">
            {activeTab === 'datasource' && <DataSourceList />}
            {activeTab === 'knowledge' && <KnowledgeList />}
            {activeTab === 'agentConfig' && renderAgentConfigContent()}
          </div>
        </div>
      </Modal>
      <SlidePanel />
    </>
  )
}

export default SettingsPage

import React from 'react'
import { DatabaseOutlined, BookOutlined, SettingOutlined } from '@ant-design/icons'
import { useSettingsStore } from '../../stores/settingsStore'

const SettingsSidebar: React.FC = () => {
  const { activeTab, setActiveTab } = useSettingsStore()

  const tabs = [
    { key: 'datasource', label: '数据源', icon: <DatabaseOutlined /> },
    { key: 'knowledge', label: '知识', icon: <BookOutlined /> },
    { key: 'agentConfig', label: 'Agent配置', icon: <SettingOutlined /> },
  ]

  return (
    <div className="settings-sidebar">
      {tabs.map((tab) => (
        <div
          key={tab.key}
          className={`settings-tab ${activeTab === tab.key ? 'active' : ''}`}
          onClick={() => setActiveTab(tab.key as 'datasource' | 'knowledge' | 'agentConfig')}
        >
          {tab.icon}
          <span>{tab.label}</span>
        </div>
      ))}
    </div>
  )
}

export default SettingsSidebar

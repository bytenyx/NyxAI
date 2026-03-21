import React, { useEffect } from 'react'
import { Modal } from 'antd'
import { useSettingsStore } from '../../stores/settingsStore'
import SettingsSidebar from './SettingsSidebar'
import DataSourceList from './DataSourceList'
import KnowledgeList from './KnowledgeList'
import SlidePanel from './SlidePanel'
import { datasourceApi } from '../../services/datasourceApi'
import { knowledgeApi } from '../../services/knowledgeApi'

const SettingsPage: React.FC = () => {
  const {
    isOpen,
    closeSettings,
    activeTab,
    setDatasources,
    setKnowledge,
    setKnowledgeTags,
  } = useSettingsStore()

  useEffect(() => {
    if (isOpen) {
      loadData()
    }
  }, [isOpen])

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
            {activeTab === 'datasource' ? <DataSourceList /> : <KnowledgeList />}
          </div>
        </div>
      </Modal>
      <SlidePanel />
    </>
  )
}

export default SettingsPage

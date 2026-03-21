import React, { useEffect } from 'react'
import { Button, message } from 'antd'
import { SettingOutlined } from '@ant-design/icons'
import { useSessionStore } from '../../stores/sessionStore'
import { useSettingsStore } from '../../stores/settingsStore'
import SessionToolbar from './SessionToolbar'
import SessionList from './SessionList'
import { sessionsApi } from '../../services/api'

const SessionSidebar: React.FC = () => {
  const {
    sessions,
    currentSession,
    searchQuery,
    setSessions,
    setCurrentSession,
    setSearchQuery,
    removeSession,
  } = useSessionStore()

  const { openSettings } = useSettingsStore()

  useEffect(() => {
    loadSessions()
  }, [])

  const loadSessions = async () => {
    try {
      const response = await sessionsApi.list()
      setSessions(response.data)
    } catch (error) {
      console.error('Failed to load sessions:', error)
    }
  }

  const handleNewSession = async () => {
    try {
      const response = await sessionsApi.create({
        trigger_type: 'manual',
        trigger_source: 'user',
      })
      setCurrentSession(response.data)
      loadSessions()
    } catch (error) {
      console.error('Failed to create session:', error)
      message.error('创建会话失败')
    }
  }

  const handleDeleteSession = async (sessionId: string) => {
    try {
      await sessionsApi.delete(sessionId)
      removeSession(sessionId)
      message.success('删除成功')
    } catch (error) {
      console.error('Failed to delete session:', error)
      message.error('删除失败')
    }
  }

  const filteredSessions = searchQuery
    ? sessions.filter((s) => s.title?.toLowerCase().includes(searchQuery.toLowerCase()))
    : sessions

  return (
    <div className="session-sidebar">
      <div className="session-sidebar-header">
        <h2>NyxAI</h2>
      </div>

      <SessionToolbar
        searchQuery={searchQuery}
        onSearch={setSearchQuery}
        onNewSession={handleNewSession}
      />

      <SessionList
        sessions={filteredSessions}
        currentSessionId={currentSession?.id || null}
        onSelect={(s) => setCurrentSession(s as unknown as typeof currentSession)}
        onDelete={handleDeleteSession}
      />

      <div className="session-sidebar-footer">
        <Button icon={<SettingOutlined />} block onClick={openSettings}>
          设置
        </Button>
      </div>
    </div>
  )
}

export default SessionSidebar

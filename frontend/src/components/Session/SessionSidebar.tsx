import React, { useEffect, useState } from 'react'
import { Button, message, Spin } from 'antd'
import { SettingOutlined } from '@ant-design/icons'
import { useSessionStore } from '../../stores/sessionStore'
import { useSettingsStore } from '../../stores/settingsStore'
import SessionToolbar from './SessionToolbar'
import SessionList from './SessionList'
import { sessionsApi } from '../../services/api'
import type { SessionListItem } from '../../types'

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

  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(true)
  const [totalCount, setTotalCount] = useState(0)

  useEffect(() => {
    loadSessions()
  }, [])

  const loadSessions = async (pageNum = 1, append = false) => {
    try {
      setLoading(true)
      const response = await sessionsApi.list(pageNum, 20)
      
      if (append) {
        setSessions([...sessions, ...response.items])
      } else {
        setSessions(response.items)
      }
      
      setTotalCount(response.total)
      setHasMore(response.page < response.total_pages)
      setPage(pageNum)
    } catch (error) {
      console.error('Failed to load sessions:', error)
      message.error('加载会话列表失败')
    } finally {
      setLoading(false)
    }
  }

  const handleLoadMore = () => {
    if (!loading && hasMore) {
      loadSessions(page + 1, true)
    }
  }

  const handleNewSession = async () => {
    try {
      const response = await sessionsApi.create({
        trigger_type: 'manual',
        trigger_source: 'user',
        title: '新会话',
      })
      setCurrentSession(response)
      loadSessions(1, false)
    } catch (error) {
      console.error('Failed to create session:', error)
      message.error('创建会话失败')
    }
  }

  const handleDeleteSession = async (sessionId: string) => {
    try {
      await sessionsApi.delete(sessionId)
      removeSession(sessionId)
      setTotalCount(totalCount - 1)
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

      {hasMore && !searchQuery && (
        <div className="session-sidebar-footer">
          <Button
            block
            onClick={handleLoadMore}
            loading={loading}
            disabled={!hasMore}
          >
            {loading ? '加载中...' : `加载更多 (${sessions.length}/${totalCount})`}
          </Button>
        </div>
      )}

      <div className="session-sidebar-footer">
        <Button icon={<SettingOutlined />} block onClick={openSettings}>
          设置
        </Button>
      </div>
    </div>
  )
}

export default SessionSidebar

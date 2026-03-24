import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import ChatWindow from '../ChatWindow'
import { useSessionStore } from '../../stores/sessionStore'
import { useAgentStore } from '../../stores/agentStore'

vi.mock('../../stores/sessionStore')
vi.mock('../../stores/agentStore')
vi.mock('../../services/websocket')

describe('ChatWindow', () => {
  const mockSetConnected = vi.fn()
  const mockHandleMessage = vi.fn()
  const mockReset = vi.fn()
  const mockWs = {
    connect: vi.fn().mockResolvedValue(undefined),
    disconnect: vi.fn(),
    on: vi.fn(),
    onConnection: vi.fn(),
    sendChat: vi.fn(),
    isConnected: vi.fn().mockReturnValue(true),
  }

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useAgentStore).mockReturnValue({
      agents: {},
      currentAgent: null,
      timeline: [],
      sequence: 0,
      isConnected: false,
      setCurrentAgent: vi.fn(),
      handleMessage: mockHandleMessage,
      setConnected: mockSetConnected,
      reset: mockReset,
    })

    vi.doMock('../../services/websocket', () => ({
      getWebSocket: vi.fn().mockReturnValue(mockWs),
    }))
  })

  describe('empty state', () => {
    it('renders empty state when no session selected', () => {
      vi.mocked(useSessionStore).mockReturnValue({
        sessions: [],
        currentSession: null,
        isLoading: false,
        searchQuery: '',
        messages: [],
        loading: false,
        setSessions: vi.fn(),
        setCurrentSession: vi.fn(),
        addSession: vi.fn(),
        updateSession: vi.fn(),
        removeSession: vi.fn(),
        setLoading: vi.fn(),
        setSearchQuery: vi.fn(),
        addMessage: vi.fn(),
        clearMessages: vi.fn(),
      })

      render(<ChatWindow />)

      expect(screen.getByText('选择或创建一个会话开始对话')).toBeInTheDocument()
    })
  })

  describe('with active session', () => {
    const mockSession = {
      id: 'test-session-1',
      title: 'Test Session',
      trigger_type: 'chat',
      trigger_source: 'user-input',
      status: 'investigating',
      message_count: 0,
      created_at: new Date(),
      updated_at: new Date(),
    }

    beforeEach(() => {
      vi.mocked(useSessionStore).mockReturnValue({
        sessions: [mockSession],
        currentSession: mockSession,
        isLoading: false,
        searchQuery: '',
        messages: [],
        loading: false,
        setSessions: vi.fn(),
        setCurrentSession: vi.fn(),
        addSession: vi.fn(),
        updateSession: vi.fn(),
        removeSession: vi.fn(),
        setLoading: vi.fn(),
        setSearchQuery: vi.fn(),
        addMessage: vi.fn(),
        clearMessages: vi.fn(),
      })
    })

    it('renders chat interface when session is selected', () => {
      render(<ChatWindow />)

      expect(screen.queryByText('选择或创建一个会话开始对话')).not.toBeInTheDocument()
      expect(screen.getByPlaceholderText('输入消息...')).toBeInTheDocument()
      expect(screen.getByText('发送')).toBeInTheDocument()
    })

    it('connects to websocket on mount', () => {
      render(<ChatWindow />)

      expect(mockWs.connect).toHaveBeenCalledWith('test-session-1')
    })

    it('sends message when send button is clicked', async () => {
      render(<ChatWindow />)

      const input = screen.getByPlaceholderText('输入消息...')
      const sendButton = screen.getByText('发送')

      fireEvent.change(input, { target: { value: 'Test message' } })
      fireEvent.click(sendButton)

      await waitFor(() => {
        expect(mockWs.sendChat).toHaveBeenCalledWith('Test message')
      })
    })

    it('sends message when Enter key is pressed without shift', async () => {
      render(<ChatWindow />)

      const input = screen.getByPlaceholderText('输入消息...')

      fireEvent.change(input, { target: { value: 'Test message' } })
      fireEvent.keyDown(input, { key: 'Enter', shiftKey: false })

      await waitFor(() => {
        expect(mockWs.sendChat).toHaveBeenCalledWith('Test message')
      })
    })

    it('does not send message when Enter key is pressed with shift', async () => {
      render(<ChatWindow />)

      const input = screen.getByPlaceholderText('输入消息...')

      fireEvent.change(input, { target: { value: 'Test message\n' } })
      fireEvent.keyDown(input, { key: 'Enter', shiftKey: true })

      await waitFor(() => {
        expect(mockWs.sendChat).not.toHaveBeenCalled()
      })
    })

    it('clears input after sending message', async () => {
      render(<ChatWindow />)

      const input = screen.getByPlaceholderText('输入消息...') as HTMLTextAreaElement
      const sendButton = screen.getByText('发送')

      fireEvent.change(input, { target: { value: 'Test message' } })
      fireEvent.click(sendButton)

      await waitFor(() => {
        expect(input.value).toBe('')
      })
    })

    it('disables send button when not connected', () => {
      vi.mocked(useAgentStore).mockReturnValue({
        agents: {},
        currentAgent: null,
        timeline: [],
        sequence: 0,
        isConnected: false,
        setCurrentAgent: vi.fn(),
        handleMessage: mockHandleMessage,
        setConnected: mockSetConnected,
        reset: mockReset,
      })

      render(<ChatWindow />)

      const sendButton = screen.getByText('发送')
      expect(sendButton).toBeDisabled()
    })

    it('does not send empty message', async () => {
      render(<ChatWindow />)

      const input = screen.getByPlaceholderText('输入消息...')
      const sendButton = screen.getByText('发送')

      fireEvent.change(input, { target: { value: '   ' } })
      fireEvent.click(sendButton)

      await waitFor(() => {
        expect(mockWs.sendChat).not.toHaveBeenCalled()
      })
    })
  })

  describe('cleanup', () => {
    const mockSession = {
      id: 'test-session-1',
      title: 'Test Session',
      trigger_type: 'chat',
      trigger_source: 'user-input',
      status: 'investigating',
      message_count: 0,
      created_at: new Date(),
      updated_at: new Date(),
    }

    beforeEach(() => {
      vi.mocked(useSessionStore).mockReturnValue({
        sessions: [mockSession],
        currentSession: mockSession,
        isLoading: false,
        searchQuery: '',
        messages: [],
        loading: false,
        setSessions: vi.fn(),
        setCurrentSession: vi.fn(),
        addSession: vi.fn(),
        updateSession: vi.fn(),
        removeSession: vi.fn(),
        setLoading: vi.fn(),
        setSearchQuery: vi.fn(),
        addMessage: vi.fn(),
        clearMessages: vi.fn(),
      })
    })

    it('disconnects websocket on unmount', () => {
      const { unmount } = render(<ChatWindow />)

      unmount()

      expect(mockWs.disconnect).toHaveBeenCalled()
    })

    it('resets agent store on session change', () => {
      const { rerender } = render(<ChatWindow />)

      const newSession = { ...mockSession, id: 'test-session-2' }
      vi.mocked(useSessionStore).mockReturnValue({
        sessions: [mockSession, newSession],
        currentSession: newSession,
        isLoading: false,
        searchQuery: '',
        messages: [],
        loading: false,
        setSessions: vi.fn(),
        setCurrentSession: vi.fn(),
        addSession: vi.fn(),
        updateSession: vi.fn(),
        removeSession: vi.fn(),
        setLoading: vi.fn(),
        setSearchQuery: vi.fn(),
        addMessage: vi.fn(),
        clearMessages: vi.fn(),
      })

      rerender(<ChatWindow />)

      expect(mockReset).toHaveBeenCalled()
    })
  })
})
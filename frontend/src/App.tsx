import React from 'react'
import { ConfigProvider, Layout, theme } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import SessionSidebar from './components/Session/SessionSidebar'
import ChatWindow from './components/Chat/ChatWindow'
import SettingsPage from './components/Settings/SettingsPage'
import './App.css'

const { Sider, Content } = Layout

const App: React.FC = () => {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: theme.defaultAlgorithm,
      }}
    >
      <Layout className="app-layout">
        <Sider width={280} className="app-sider">
          <SessionSidebar />
        </Sider>
        <Content className="app-content">
          <ChatWindow />
        </Content>
        <SettingsPage />
      </Layout>
    </ConfigProvider>
  )
}

export default App

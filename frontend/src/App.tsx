import { ConfigProvider, Layout, theme } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { ChatWindow, MessageInput } from './components/Chat/ChatWindow'

const { Content, Footer } = Layout

function App() {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: theme.defaultAlgorithm,
      }}
    >
      <Layout style={{ minHeight: '100vh' }}>
        <Content style={{ padding: 24, maxWidth: 1200, margin: '0 auto', width: '100%' }}>
          <div style={{ marginBottom: 16, textAlign: 'center' }}>
            <h1 style={{ margin: 0, fontSize: 24 }}>NyxAI 运维智能体</h1>
            <p style={{ color: '#666', margin: '8px 0 0' }}>多Agent协作的故障自愈系统</p>
          </div>
          <ChatWindow />
        </Content>
        <Footer style={{ background: '#fff', padding: 16, borderTop: '1px solid #f0f0f0' }}>
          <div style={{ maxWidth: 1200, margin: '0 auto' }}>
            <MessageInput />
          </div>
        </Footer>
      </Layout>
    </ConfigProvider>
  )
}

export default App

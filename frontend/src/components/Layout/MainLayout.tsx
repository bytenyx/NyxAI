import { useEffect, useState } from 'react'
import { Layout, Menu, theme, Breadcrumb } from 'antd'
import {
  DashboardOutlined,
  AlertOutlined,
  LineChartOutlined,
  NodeIndexOutlined,
  MedicineBoxOutlined,
  SettingOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons'
import { Outlet, useLocation, useNavigate, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { wsService } from '@services/websocket'
import LanguageSwitcher from '@components/LanguageSwitcher'
import styles from './styles.module.css'

const { Header, Sider, Content } = Layout

const MainLayout = () => {
  const { t } = useTranslation()
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken()

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: t('nav.dashboard'),
    },
    {
      key: '/anomalies',
      icon: <AlertOutlined />,
      label: t('nav.anomalies'),
    },
    {
      key: '/metrics',
      icon: <LineChartOutlined />,
      label: t('nav.metrics'),
    },
    {
      key: '/rca',
      icon: <NodeIndexOutlined />,
      label: t('nav.rca'),
    },
    {
      key: '/recovery',
      icon: <MedicineBoxOutlined />,
      label: t('nav.recovery'),
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: t('nav.settings'),
    },
  ]

  // 连接 WebSocket
  useEffect(() => {
    wsService.connect()

    return () => {
      wsService.disconnect()
    }
  }, [])

  // 生成面包屑
  const getBreadcrumbItems = () => {
    const pathSnippets = location.pathname.split('/').filter((i) => i)
    const breadcrumbItems = [{ title: <Link to="/">{t('nav.dashboard')}</Link> }]

    let currentPath = ''
    pathSnippets.forEach((snippet) => {
      currentPath += `/${snippet}`
      const menuItem = menuItems.find((item) => item.key === currentPath)
      if (menuItem) {
        breadcrumbItems.push({
          title: <Link to={currentPath}>{menuItem.label}</Link>,
        })
      }
    })

    return breadcrumbItems
  }

  return (
    <Layout className={styles.layout}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        theme="light"
        className={styles.sider}
      >
        <div className={styles.logo}>
          {collapsed ? 'N' : t('app.name')}
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          className={styles.menu}
        />
      </Sider>

      <Layout>
        <Header className={styles.header} style={{ background: colorBgContainer }}>
          <div className={styles.headerLeft}>
            <div
              className={styles.collapseBtn}
              onClick={() => setCollapsed(!collapsed)}
            >
              {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            </div>
            <Breadcrumb items={getBreadcrumbItems()} />
          </div>

          <div className={styles.headerRight}>
            <LanguageSwitcher />
          </div>
        </Header>

        <Content
          className={styles.content}
          style={{
            background: colorBgContainer,
            borderRadius: borderRadiusLG,
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}

export default MainLayout

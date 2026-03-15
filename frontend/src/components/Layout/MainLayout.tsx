import { useEffect, useState } from 'react'
import { Layout, Menu, Avatar, Dropdown, Badge, theme, Breadcrumb } from 'antd'
import {
  DashboardOutlined,
  AlertOutlined,
  LineChartOutlined,
  NodeIndexOutlined,
  MedicineBoxOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined,
  BellOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons'
import { Outlet, useLocation, useNavigate, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '@store/authStore'
import { wsService } from '@services/websocket'
import { authApi } from '@services/api'
import LanguageSwitcher from '@components/LanguageSwitcher'
import styles from './styles.module.css'

const { Header, Sider, Content } = Layout

const MainLayout = () => {
  const { t } = useTranslation()
  const [collapsed, setCollapsed] = useState(false)
  const [notificationCount, setNotificationCount] = useState(0)
  const location = useLocation()
  const navigate = useNavigate()
  const { user, clearAuth } = useAuthStore()
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken()

  // 使用 useMemo 缓存 menuItems
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
    
    // 订阅异常检测消息
    const unsubscribe = wsService.subscribe('anomaly_detected', () => {
      setNotificationCount((prev) => prev + 1)
    })

    return () => {
      unsubscribe()
      wsService.disconnect()
    }
  }, [])

  const handleLogout = async () => {
    try {
      await authApi.logout()
    } finally {
      clearAuth()
      navigate('/login')
    }
  }

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: t('user.profile'),
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: t('user.logout'),
      onClick: handleLogout,
    },
  ]

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
            <Badge count={notificationCount} size="small">
              <BellOutlined
                className={styles.icon}
                onClick={() => setNotificationCount(0)}
              />
            </Badge>
            
            <LanguageSwitcher />
            
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <div className={styles.userInfo}>
                <Avatar icon={<UserOutlined />} src={user?.avatar} />
                {!collapsed && (
                  <span className={styles.username}>{user?.username}</span>
                )}
              </div>
            </Dropdown>
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

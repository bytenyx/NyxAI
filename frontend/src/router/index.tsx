import { createBrowserRouter, Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '@store/authStore'
import MainLayout from '@components/Layout/MainLayout'
import LoginPage from '@pages/Login'
import DashboardPage from '@pages/Dashboard'
import AnomaliesPage from '@pages/Anomalies'
import AnomalyDetailPage from '@pages/Anomalies/Detail'
import MetricsPage from '@pages/Metrics'
import RCAPage from '@pages/RCA'
import RecoveryPage from '@pages/Recovery'
import SettingsPage from '@pages/Settings'

// 路由守卫组件
const ProtectedRoute = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />
}

// 已登录用户访问登录页的重定向
const PublicRoute = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  return !isAuthenticated ? <Outlet /> : <Navigate to="/" replace />
}

export const router = createBrowserRouter([
  {
    element: <PublicRoute />,
    children: [
      {
        path: '/login',
        element: <LoginPage />,
      },
    ],
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <MainLayout />,
        children: [
          {
            path: '/',
            element: <DashboardPage />,
          },
          {
            path: '/dashboard',
            element: <DashboardPage />,
          },
          {
            path: '/anomalies',
            element: <AnomaliesPage />,
          },
          {
            path: '/anomalies/:id',
            element: <AnomalyDetailPage />,
          },
          {
            path: '/metrics',
            element: <MetricsPage />,
          },
          {
            path: '/rca',
            element: <RCAPage />,
          },
          {
            path: '/recovery',
            element: <RecoveryPage />,
          },
          {
            path: '/settings',
            element: <SettingsPage />,
          },
        ],
      },
    ],
  },
  {
    path: '*',
    element: <Navigate to="/" replace />,
  },
])

export default router

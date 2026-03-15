import { createBrowserRouter, Navigate } from 'react-router-dom'
import MainLayout from '@components/Layout/MainLayout'
import DashboardPage from '@pages/Dashboard'
import AnomaliesPage from '@pages/Anomalies'
import AnomalyDetailPage from '@pages/Anomalies/Detail'
import MetricsPage from '@pages/Metrics'
import RCAPage from '@pages/RCA'
import RecoveryPage from '@pages/Recovery'
import SettingsPage from '@pages/Settings'

export const router = createBrowserRouter([
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
  {
    path: '*',
    element: <Navigate to="/" replace />,
  },
])

export default router

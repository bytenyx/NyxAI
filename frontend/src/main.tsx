import React from 'react'
import ReactDOM from 'react-dom/client'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import enUS from 'antd/locale/en_US'
import { RouterProvider } from 'react-router-dom'
import { router } from './router'
import './i18n'
import './styles/index.css'
import i18n from './i18n'

// 根据当前语言设置 Ant Design 的 locale
const getAntdLocale = () => {
  const lang = i18n.language
  if (lang === 'en-US') {
    return enUS
  }
  return zhCN
}

const Root = () => {
  const [locale, setLocale] = React.useState(getAntdLocale())

  React.useEffect(() => {
    const handleLanguageChanged = () => {
      setLocale(getAntdLocale())
    }
    i18n.on('languageChanged', handleLanguageChanged)
    return () => {
      i18n.off('languageChanged', handleLanguageChanged)
    }
  }, [])

  return (
    <ConfigProvider
      locale={locale}
      theme={{
        token: {
          colorPrimary: '#1677ff',
          borderRadius: 6,
        },
      }}
    >
      <RouterProvider router={router} />
    </ConfigProvider>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>,
)

import { useState } from 'react'
import { Form, Input, Button, Card, message, Spin } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '@store/authStore'
import { authApi } from '@services/api'
import { LoginParams } from '@types/index'
import LanguageSwitcher from '@components/LanguageSwitcher'
import styles from './styles.module.css'

const LoginPage = () => {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(false)
  const setAuth = useAuthStore((state) => state.setAuth)

  const handleLogin = async (values: LoginParams) => {
    setLoading(true)
    try {
      const response = await authApi.login(values)
      if (response.data) {
        setAuth(response.data)
        message.success(t('login.success'))
      }
    } catch (error) {
      message.error(t('login.error'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.languageSwitcher}>
        <LanguageSwitcher />
      </div>
      <Card className={styles.card} bordered={false}>
        <div className={styles.header}>
          <h1 className={styles.title}>{t('app.name')}</h1>
          <p className={styles.subtitle}>{t('app.title')}</p>
        </div>
        
        <Spin spinning={loading}>
          <Form
            name="login"
            onFinish={handleLogin}
            autoComplete="off"
            size="large"
          >
            <Form.Item
              name="username"
              rules={[{ required: true, message: t('login.username') }]}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder={t('login.username')}
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[{ required: true, message: t('login.password') }]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder={t('login.password')}
              />
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                block
                loading={loading}
              >
                {t('login.submit')}
              </Button>
            </Form.Item>
          </Form>
        </Spin>

        <div className={styles.footer}>
          <p>{t('login.defaultAccount')}</p>
        </div>
      </Card>
    </div>
  )
}

export default LoginPage

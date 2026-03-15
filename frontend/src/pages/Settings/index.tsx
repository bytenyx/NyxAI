import { useState } from 'react'
import {
  Card,
  Tabs,
  Form,
  Input,
  Button,
  Switch,
  Select,
  message,
} from 'antd'
import {
  SettingOutlined,
  BellOutlined,
  SafetyOutlined,
} from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import i18n from '../../i18n'
import styles from './styles.module.css'

const { TabPane } = Tabs
const { Option } = Select

const SettingsPage = () => {
  const { t } = useTranslation()
  const [generalForm] = Form.useForm()
  const [notificationForm] = Form.useForm()

  const handleGeneralSubmit = (values: { language: string }) => {
    // 切换语言
    if (values.language) {
      i18n.changeLanguage(values.language)
    }
    message.success(t('settings.general.saveSuccess'))
  }

  const handleNotificationSubmit = () => {
    message.success(t('notifications.saveSuccess'))
  }

  return (
    <Card
      title={
        <span>
          <SettingOutlined /> {t('settings.title')}
        </span>
      }
    >
      <Tabs defaultActiveKey="general">
        <TabPane
          tab={
            <span>
              <SettingOutlined />
              {t('settings.tabs.general')}
            </span>
          }
          key="general"
        >
          <Form
            form={generalForm}
            layout="vertical"
            onFinish={handleGeneralSubmit}
            initialValues={{
              systemName: 'NyxAI',
              timezone: 'Asia/Shanghai',
              language: i18n.language || 'zh-CN',
              autoRefresh: true,
              refreshInterval: 30,
            }}
          >
            <Form.Item
              label={t('settings.general.systemName')}
              name="systemName"
              rules={[{ required: true }]}
            >
              <Input />
            </Form.Item>

            <Form.Item
              label={t('settings.general.timezone')}
              name="timezone"
              rules={[{ required: true }]}
            >
              <Select>
                <Option value="Asia/Shanghai">{t('settings.timezone.shanghai')}</Option>
                <Option value="Asia/Tokyo">{t('settings.timezone.tokyo')}</Option>
                <Option value="America/New_York">{t('settings.timezone.newYork')}</Option>
                <Option value="Europe/London">{t('settings.timezone.london')}</Option>
                <Option value="UTC">{t('settings.timezone.utc')}</Option>
              </Select>
            </Form.Item>

            <Form.Item
              label={t('settings.general.language')}
              name="language"
              rules={[{ required: true }]}
            >
              <Select>
                <Option value="zh-CN">{t('settings.language.zhCN')}</Option>
                <Option value="en-US">{t('settings.language.enUS')}</Option>
              </Select>
            </Form.Item>

            <Form.Item
              label={t('settings.general.autoRefresh')}
              name="autoRefresh"
              valuePropName="checked"
            >
              <Switch />
            </Form.Item>

            <Form.Item
              label={t('settings.general.refreshInterval')}
              name="refreshInterval"
            >
              <Select>
                <Option value={10}>{t('settings.refreshInterval.10s')}</Option>
                <Option value={30}>{t('settings.refreshInterval.30s')}</Option>
                <Option value={60}>{t('settings.refreshInterval.1m')}</Option>
                <Option value={300}>{t('settings.refreshInterval.5m')}</Option>
              </Select>
            </Form.Item>

            <Form.Item>
              <Button type="primary" htmlType="submit">
                {t('common.save')}
              </Button>
            </Form.Item>
          </Form>
        </TabPane>

        <TabPane
          tab={
            <span>
              <BellOutlined />
              {t('settings.tabs.notifications')}
            </span>
          }
          key="notifications"
        >
          <Form
            form={notificationForm}
            layout="vertical"
            onFinish={handleNotificationSubmit}
            initialValues={{
              emailEnabled: true,
              webhookEnabled: false,
              smsEnabled: false,
              anomalyNotify: true,
              recoveryNotify: true,
            }}
          >
            <Form.Item
              label={t('notifications.email.enabled')}
              name="emailEnabled"
              valuePropName="checked"
            >
              <Switch />
            </Form.Item>

            <Form.Item
              label={t('notifications.email.server')}
              name="emailServer"
            >
              <Input placeholder="smtp.example.com" />
            </Form.Item>

            <Form.Item
              label={t('notifications.webhook.enabled')}
              name="webhookEnabled"
              valuePropName="checked"
            >
              <Switch />
            </Form.Item>

            <Form.Item
              label={t('notifications.webhook.url')}
              name="webhookUrl"
            >
              <Input placeholder="https://example.com/webhook" />
            </Form.Item>

            <Form.Item
              label={t('notifications.sms.enabled')}
              name="smsEnabled"
              valuePropName="checked"
            >
              <Switch />
            </Form.Item>

            <Form.Item
              label={t('notifications.events.anomaly')}
              name="anomalyNotify"
              valuePropName="checked"
            >
              <Switch />
            </Form.Item>

            <Form.Item
              label={t('notifications.events.recovery')}
              name="recoveryNotify"
              valuePropName="checked"
            >
              <Switch />
            </Form.Item>

            <Form.Item>
              <Button type="primary" htmlType="submit">
                {t('common.save')}
              </Button>
            </Form.Item>
          </Form>
        </TabPane>

        <TabPane
          tab={
            <span>
              <SafetyOutlined />
              {t('settings.tabs.security')}
            </span>
          }
          key="security"
        >
          <Form layout="vertical">
            <Form.Item
              label={t('security.minPasswordLength')}
              name="minPasswordLength"
              initialValue={8}
            >
              <Input type="number" />
            </Form.Item>

            <Form.Item
              label={t('security.maxLoginAttempts')}
              name="maxLoginAttempts"
              initialValue={5}
            >
              <Input type="number" />
            </Form.Item>

            <Form.Item
              label={t('security.sessionTimeout')}
              name="sessionTimeout"
              initialValue={30}
            >
              <Input type="number" />
            </Form.Item>

            <Form.Item
              label={t('security.enable2FA')}
              name="enable2FA"
              valuePropName="checked"
              initialValue={false}
            >
              <Switch />
            </Form.Item>

            <Form.Item>
              <Button type="primary">{t('common.save')}</Button>
            </Form.Item>
          </Form>
        </TabPane>
      </Tabs>
    </Card>
  )
}

export default SettingsPage

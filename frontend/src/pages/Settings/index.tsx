import { useState, useEffect } from 'react'
import {
  Card,
  Tabs,
  Form,
  Input,
  Button,
  Switch,
  Select,
  message,
  Table,
  Space,
  Modal,
  Tag,
  Popconfirm,
} from 'antd'
import {
  SettingOutlined,
  UserOutlined,
  BellOutlined,
  SafetyOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
} from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import i18n from '../../i18n'
import { userApi } from '@services/api'
import { User, PaginationData } from '@types/index'
import dayjs from 'dayjs'
import styles from './styles.module.css'

const { TabPane } = Tabs
const { Option } = Select

const SettingsPage = () => {
  const { t } = useTranslation()
  const [generalForm] = Form.useForm()
  const [notificationForm] = Form.useForm()
  const [userModalVisible, setUserModalVisible] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [users, setUsers] = useState<PaginationData<User> | null>(null)
  const [userLoading, setUserLoading] = useState(false)

  const fetchUsers = async () => {
    setUserLoading(true)
    try {
      const res = await userApi.getList({ page: 1, pageSize: 100 })
      setUsers(res.data)
    } catch (error) {
      message.error(t('errors.fetchFailed'))
    } finally {
      setUserLoading(false)
    }
  }

  useEffect(() => {
    fetchUsers()
  }, [])

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

  const handleAddUser = () => {
    setEditingUser(null)
    setUserModalVisible(true)
  }

  const handleEditUser = (user: User) => {
    setEditingUser(user)
    setUserModalVisible(true)
  }

  const handleDeleteUser = async (id: string) => {
    try {
      await userApi.delete(id)
      message.success(t('userManagement.deleteSuccess'))
      fetchUsers()
    } catch (error) {
      message.error(t('errors.operationFailed'))
    }
  }

  const handleUserModalSubmit = async (values: { username: string; email: string; role: string; password?: string }) => {
    try {
      if (editingUser) {
        await userApi.update(editingUser.id, values)
        message.success(t('userManagement.updateSuccess'))
      } else {
        await userApi.create({ ...values, password: values.password || '123456' })
        message.success(t('userManagement.createSuccess'))
      }
      setUserModalVisible(false)
      fetchUsers()
    } catch (error) {
      message.error(t('errors.operationFailed'))
    }
  }

  const userColumns = [
    {
      title: t('userManagement.fields.username'),
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: t('userManagement.fields.email'),
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: t('userManagement.fields.role'),
      dataIndex: 'role',
      key: 'role',
      render: (role: string) => {
        const roleMap: Record<string, { color: string; text: string }> = {
          admin: { color: 'red', text: t('user.role.admin') },
          operator: { color: 'blue', text: t('user.role.operator') },
          viewer: { color: 'green', text: t('user.role.viewer') },
        }
        const { color, text } = roleMap[role] || { color: 'default', text: role }
        return <Tag color={color}>{text}</Tag>
      },
    },
    {
      title: t('userManagement.fields.createdAt'),
      dataIndex: 'createdAt',
      key: 'createdAt',
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: t('common.action'),
      key: 'action',
      render: (_: unknown, record: User) => (
        <Space size="small">
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEditUser(record)}
          >
            {t('common.edit')}
          </Button>
          <Popconfirm
            title={t('userManagement.deleteConfirm')}
            onConfirm={() => handleDeleteUser(record.id)}
            okText={t('common.confirm')}
            cancelText={t('common.cancel')}
          >
            <Button type="text" danger icon={<DeleteOutlined />}>
              {t('common.delete')}
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  // 模拟用户数据
  const mockUsers: User[] = [
    {
      id: '1',
      username: 'admin',
      email: 'admin@nyxai.com',
      role: 'admin',
      createdAt: '2024-01-01T00:00:00Z',
    },
    {
      id: '2',
      username: 'operator1',
      email: 'operator1@nyxai.com',
      role: 'operator',
      createdAt: '2024-02-15T00:00:00Z',
    },
    {
      id: '3',
      username: 'viewer1',
      email: 'viewer1@nyxai.com',
      role: 'viewer',
      createdAt: '2024-03-01T00:00:00Z',
    },
  ]

  return (
    <Card
      title={
        <Space>
          <SettingOutlined />
          <span>{t('settings.title')}</span>
        </Space>
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
              <UserOutlined />
              {t('settings.tabs.users')}
            </span>
          }
          key="users"
        >
          <div className={styles.userHeader}>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAddUser}>
              {t('userManagement.addUser')}
            </Button>
          </div>
          <Table
            columns={userColumns}
            dataSource={mockUsers}
            rowKey="id"
            loading={userLoading}
            pagination={false}
          />
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

      <Modal
        title={editingUser ? t('userManagement.editUser') : t('userManagement.addUser')}
        open={userModalVisible}
        onCancel={() => setUserModalVisible(false)}
        footer={null}
      >
        <Form
          layout="vertical"
          onFinish={handleUserModalSubmit}
          initialValues={editingUser || { role: 'viewer' }}
        >
          <Form.Item
            label={t('userManagement.fields.username')}
            name="username"
            rules={[{ required: true, message: t('userManagement.fields.username') }]}
          >
            <Input disabled={!!editingUser} />
          </Form.Item>

          <Form.Item
            label={t('userManagement.fields.email')}
            name="email"
            rules={[
              { required: true, message: t('userManagement.fields.email') },
              { type: 'email', message: 'Email' },
            ]}
          >
            <Input />
          </Form.Item>

          <Form.Item
            label={t('userManagement.fields.role')}
            name="role"
            rules={[{ required: true, message: t('userManagement.fields.role') }]}
          >
            <Select>
              <Option value="admin">{t('user.role.admin')}</Option>
              <Option value="operator">{t('user.role.operator')}</Option>
              <Option value="viewer">{t('user.role.viewer')}</Option>
            </Select>
          </Form.Item>

          {!editingUser && (
            <Form.Item
              label={t('userManagement.fields.password')}
              name="password"
              rules={[{ required: true, message: t('userManagement.fields.password') }]}
            >
              <Input.Password placeholder={t('userManagement.passwordPlaceholder')} />
            </Form.Item>
          )}

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                {editingUser ? t('common.edit') : t('common.create')}
              </Button>
              <Button onClick={() => setUserModalVisible(false)}>{t('common.cancel')}</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}

export default SettingsPage

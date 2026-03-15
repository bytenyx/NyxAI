import { Dropdown, Button } from 'antd'
import { GlobalOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import i18n from '../../i18n'

const LanguageSwitcher = () => {
  const { t } = useTranslation()

  const items = [
    {
      key: 'zh-CN',
      label: t('settings.language.zhCN'),
      onClick: () => i18n.changeLanguage('zh-CN'),
    },
    {
      key: 'en-US',
      label: t('settings.language.enUS'),
      onClick: () => i18n.changeLanguage('en-US'),
    },
  ]

  return (
    <Dropdown menu={{ items }} placement="bottomRight">
      <Button type="text" icon={<GlobalOutlined />}>
        {i18n.language === 'en-US' ? 'EN' : '中文'}
      </Button>
    </Dropdown>
  )
}

export default LanguageSwitcher

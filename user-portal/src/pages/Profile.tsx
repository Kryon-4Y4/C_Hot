import React, { useState } from 'react'
import { Card, Avatar, Descriptions, Tag, Divider, Statistic, Row, Col, Switch, message } from 'antd'
import { UserOutlined, MailOutlined, SafetyOutlined, ClockCircleOutlined, BellOutlined } from '@ant-design/icons'
import { useAuthStore } from '../store/authStore'
import { authApi } from '../services/api'
import dayjs from 'dayjs'

const Profile: React.FC = () => {
  const { user } = useAuthStore()
  const [subscribing, setSubscribing] = useState(false)

  const getRoleTag = (role: string) => {
    const roleMap: Record<string, { text: string; color: string }> = {
      admin: { text: '管理员', color: 'red' },
      user: { text: '普通用户', color: 'blue' },
      viewer: { text: '访客', color: 'default' },
    }
    const roleInfo = roleMap[role] || { text: role, color: 'default' }
    return <Tag color={roleInfo.color}>{roleInfo.text}</Tag>
  }

  const handleSubscribeChange = async (checked: boolean) => {
    setSubscribing(true)
    try {
      await authApi.subscribeEmail(checked)
      message.success(checked ? '已订阅邮件通知' : '已取消邮件订阅')
      // 更新本地用户数据
      if (user) {
        useAuthStore.setState({
          user: { ...user, email_subscribed: checked }
        })
      }
    } catch (error) {
      message.error('设置失败')
    } finally {
      setSubscribing(false)
    }
  }

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>个人中心</h2>

      {/* 用户信息卡片 */}
      <Card style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 24 }}>
          <Avatar 
            size={80} 
            icon={<UserOutlined />} 
            style={{ background: 'linear-gradient(135deg, #1890ff 0%, #36cfc9 100%)' }}
          />
          <div style={{ marginLeft: 24 }}>
            <h3 style={{ margin: 0, fontSize: 20 }}>{user?.full_name || user?.username}</h3>
            <p style={{ margin: '8px 0 0', color: '#666' }}>
              {getRoleTag(user?.role || 'viewer')}
            </p>
          </div>
        </div>

        <Divider />

        <Descriptions title="基本信息" bordered column={{ xs: 1, sm: 2, md: 3 }}>
          <Descriptions.Item label="用户名">
            {user?.username}
          </Descriptions.Item>
          <Descriptions.Item label="邮箱">
            {user?.email}
          </Descriptions.Item>
          <Descriptions.Item label="姓名">
            {user?.full_name || '未设置'}
          </Descriptions.Item>
          <Descriptions.Item label="角色">
            {getRoleTag(user?.role || 'viewer')}
          </Descriptions.Item>
          <Descriptions.Item label="账号状态">
            <Tag color={user?.is_active ? 'success' : 'error'}>
              {user?.is_active ? '正常' : '已禁用'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="注册时间">
            {user?.created_at ? dayjs(user.created_at).format('YYYY-MM-DD HH:mm') : '-'}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* 邮件订阅设置 */}
      <Card style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h4 style={{ margin: 0 }}>
              <BellOutlined style={{ marginRight: 8 }} />
              邮件订阅
            </h4>
            <p style={{ margin: '8px 0 0', color: '#666' }}>
              订阅后，当有新数据更新时，您将收到邮件通知
            </p>
          </div>
          <Switch
            checked={user?.email_subscribed}
            onChange={handleSubscribeChange}
            loading={subscribing}
            checkedChildren="已订阅"
            unCheckedChildren="未订阅"
          />
        </div>
      </Card>

      {/* 账号统计 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="账号类型"
              value={user?.is_superuser ? '超级管理员' : (user?.role === 'admin' ? '管理员' : '普通用户')}
              prefix={<SafetyOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="最后登录"
              value={user?.last_login ? dayjs(user.last_login).format('MM-DD HH:mm') : '暂无记录'}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="邮箱状态"
              value={user?.email ? '已绑定' : '未绑定'}
              prefix={<MailOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 系统说明 */}
      <Card style={{ marginTop: 24 }}>
        <h4>关于系统</h4>
        <p style={{ color: '#666', lineHeight: 1.8 }}>
          手机维修配件外贸数据管理系统是一个公开查询平台，您可以无需登录即可查看外贸数据。
          注册账号后可订阅邮件通知，及时获取最新数据更新。
        </p>
        <p style={{ color: '#666', lineHeight: 1.8 }}>
          系统版本: v1.0.0
        </p>
      </Card>
    </div>
  )
}

export default Profile

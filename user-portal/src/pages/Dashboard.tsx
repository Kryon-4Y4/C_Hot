import React from 'react'
import { Row, Col, Card, Statistic, Table, Tag, Progress } from 'antd'
import {
  DatabaseOutlined,
  RiseOutlined,
  GlobalOutlined,
  DollarOutlined,
} from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { tradeDataApi, systemApi } from '../services/api'

const Dashboard: React.FC = () => {
  // 获取统计数据
  const { data: statsData } = useQuery({
    queryKey: ['statistics'],
    queryFn: () => tradeDataApi.getStatistics().then(res => res.data),
  })

  // 获取健康状态
  const { data: healthData } = useQuery({
    queryKey: ['health'],
    queryFn: () => systemApi.getHealth().then(res => res.data),
    refetchInterval: 30000,
  })

  // 统计卡片数据
  const statCards = [
    {
      title: '总记录数',
      value: statsData?.total_records || 0,
      icon: <DatabaseOutlined style={{ color: '#1890ff' }} />,
      color: '#e6f7ff',
    },
    {
      title: '出口总额 (USD)',
      value: statsData?.total_value_usd || 0,
      icon: <DollarOutlined style={{ color: '#52c41a' }} />,
      color: '#f6ffed',
      prefix: '$',
      formatter: (val: number) => (val / 1000000000).toFixed(2) + 'B',
    },
    {
      title: '主要贸易伙伴',
      value: statsData?.top_partners?.length || 0,
      icon: <GlobalOutlined style={{ color: '#722ed1' }} />,
      color: '#f9f0ff',
    },
    {
      title: '系统状态',
      value: healthData?.status === 'healthy' ? '正常' : '异常',
      icon: <RiseOutlined style={{ color: '#fa8c16' }} />,
      color: '#fff7e6',
    },
  ]

  // 最近数据表格列
  const columns = [
    {
      title: '年份',
      dataIndex: 'year',
      key: 'year',
      width: 80,
    },
    {
      title: 'HS编码',
      dataIndex: 'hs_code',
      key: 'hs_code',
      width: 120,
    },
    {
      title: '贸易伙伴',
      dataIndex: 'trade_partner',
      key: 'trade_partner',
    },
    {
      title: '出口金额 (USD)',
      dataIndex: 'export_value_usd',
      key: 'export_value_usd',
      render: (value: number) => `$${(value || 0).toLocaleString()}`,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'confirmed' ? 'success' : 'warning'}>
          {status === 'confirmed' ? '已确认' : '待确认'}
        </Tag>
      ),
    },
  ]

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>数据概览</h2>
      
      {/* 统计卡片 */}
      <Row gutter={[16, 16]}>
        {statCards.map((card, index) => (
          <Col xs={24} sm={12} lg={6} key={index}>
            <Card
              style={{ background: card.color, borderRadius: 8 }}
              bodyStyle={{ padding: 20 }}
            >
              <Statistic
                title={card.title}
                value={card.value}
                prefix={card.icon}
                formatter={card.formatter}
                valueStyle={{ fontSize: 28, fontWeight: 'bold' }}
              />
            </Card>
          </Col>
        ))}
      </Row>

      {/* 图表区域 */}
      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="主要贸易伙伴占比" style={{ borderRadius: 8 }}>
            {statsData?.top_partners?.map((partner: any, index: number) => (
              <div key={partner.partner} style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span>{partner.partner}</span>
                  <span>${(partner.total_value / 1000000).toFixed(1)}M</span>
                </div>
                <Progress
                  percent={Math.round((partner.total_value / (statsData?.total_value_usd || 1)) * 100)}
                  status="active"
                  strokeColor={
                    index === 0 ? '#1890ff' :
                    index === 1 ? '#52c41a' :
                    index === 2 ? '#fa8c16' : '#722ed1'
                  }
                />
              </div>
            ))}
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="HS编码分布" style={{ borderRadius: 8 }}>
            {statsData?.hs_statistics?.map((hs: any, index: number) => (
              <div key={hs.hs_code} style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span>{hs.hs_code}</span>
                  <span>{hs.count} 条记录</span>
                </div>
                <Progress
                  percent={Math.round((hs.total_value / (statsData?.total_value_usd || 1)) * 100)}
                  status="active"
                  strokeColor={index === 0 ? '#1890ff' : '#52c41a'}
                />
              </div>
            ))}
          </Card>
        </Col>
      </Row>

      {/* 最近数据 */}
      <Card title="最近数据" style={{ marginTop: 24, borderRadius: 8 }}>
        <Table
          columns={columns}
          dataSource={[]}
          rowKey="id"
          pagination={false}
          size="small"
          locale={{ emptyText: '暂无数据' }}
        />
      </Card>
    </div>
  )
}

export default Dashboard

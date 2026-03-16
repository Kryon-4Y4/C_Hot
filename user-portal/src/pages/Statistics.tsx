import React, { useState } from 'react'
import {
  Card,
  Row,
  Col,
  Select,
  Statistic,
  Table,
  Spin,
} from 'antd'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { useQuery } from '@tanstack/react-query'
import { tradeDataApi } from '../services/api'

const { Option } = Select

// 颜色配置
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d']

const Statistics: React.FC = () => {
  const [selectedYear, setSelectedYear] = useState<number | undefined>(undefined)

  // 获取统计数据
  const { data: statsData, isLoading: statsLoading } = useQuery({
    queryKey: ['statistics', selectedYear],
    queryFn: () => tradeDataApi.getStatistics(selectedYear).then(res => res.data),
  })

  // 获取年度统计
  const { data: yearStatsData, isLoading: yearStatsLoading } = useQuery({
    queryKey: ['statisticsByYear'],
    queryFn: () => tradeDataApi.getStatisticsByYear().then(res => res.data),
  })

  // 贸易伙伴表格列
  const partnerColumns = [
    {
      title: '排名',
      dataIndex: 'index',
      key: 'index',
      width: 80,
      render: (_: any, __: any, index: number) => index + 1,
    },
    {
      title: '贸易伙伴',
      dataIndex: 'partner',
      key: 'partner',
    },
    {
      title: '出口金额 (USD)',
      dataIndex: 'total_value',
      key: 'total_value',
      render: (value: number) => `$${(value || 0).toLocaleString()}`,
    },
    {
      title: '记录数',
      dataIndex: 'count',
      key: 'count',
    },
    {
      title: '占比',
      dataIndex: 'percentage',
      key: 'percentage',
      render: (_: any, record: any) => {
        const total = statsData?.total_value_usd || 1
        const percentage = ((record.total_value / total) * 100).toFixed(2)
        return `${percentage}%`
      },
    },
  ]

  // 准备饼图数据
  const pieData = statsData?.top_partners?.map((item: any) => ({
    name: item.partner,
    value: item.total_value,
  })) || []

  return (
    <Spin spinning={statsLoading || yearStatsLoading}>
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <h2 style={{ margin: 0 }}>统计分析</h2>
          <Select
            placeholder="选择年份"
            style={{ width: 150 }}
            allowClear
            value={selectedYear}
            onChange={setSelectedYear}
          >
            <Option value={2022}>2022年</Option>
            <Option value={2023}>2023年</Option>
            <Option value={2024}>2024年</Option>
          </Select>
        </div>

        {/* 统计卡片 */}
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="总记录数"
                value={statsData?.total_records || 0}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="出口总额 (USD)"
                value={statsData?.total_value_usd || 0}
                precision={2}
                valueStyle={{ color: '#52c41a' }}
                formatter={(value) => `$${Number(value).toLocaleString()}`}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="贸易伙伴数"
                value={statsData?.top_partners?.length || 0}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="HS编码种类"
                value={statsData?.hs_statistics?.length || 0}
                valueStyle={{ color: '#fa8c16' }}
              />
            </Card>
          </Col>
        </Row>

        {/* 年度趋势图 */}
        <Card title="年度出口趋势" style={{ marginTop: 24 }}>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={yearStatsData || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" />
              <YAxis
                tickFormatter={(value) => `$${(value / 1000000000).toFixed(1)}B`}
              />
              <Tooltip
                formatter={(value: number) => [`$${value.toLocaleString()}`, '出口金额']}
                labelFormatter={(label) => `${label}年`}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="total_value_usd"
                name="出口金额 (USD)"
                stroke="#1890ff"
                strokeWidth={2}
                dot={{ fill: '#1890ff' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        {/* 图表区域 */}
        <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
          <Col xs={24} lg={12}>
            <Card title="主要贸易伙伴分布">
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {pieData.map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: number) => `$${value.toLocaleString()}`} />
                </PieChart>
              </ResponsiveContainer>
            </Card>
          </Col>

          <Col xs={24} lg={12}>
            <Card title="HS编码统计">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={statsData?.hs_statistics || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="hs_code" />
                  <YAxis
                    tickFormatter={(value) => `$${(value / 1000000000).toFixed(1)}B`}
                  />
                  <Tooltip
                    formatter={(value: number) => [`$${value.toLocaleString()}`, '出口金额']}
                  />
                  <Bar dataKey="total_value" name="出口金额 (USD)" fill="#1890ff" />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          </Col>
        </Row>

        {/* 贸易伙伴详情表 */}
        <Card title="主要贸易伙伴详情" style={{ marginTop: 24 }}>
          <Table
            columns={partnerColumns}
            dataSource={statsData?.top_partners || []}
            rowKey="partner"
            pagination={false}
          />
        </Card>
      </div>
    </Spin>
  )
}

export default Statistics

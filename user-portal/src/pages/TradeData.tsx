import React, { useState } from 'react'
import {
  Table,
  Card,
  Input,
  Select,
  Button,
  Space,
  Tag,
  Popconfirm,
  message,
  Row,
  Col,
} from 'antd'
import {
  SearchOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  DeleteOutlined,
  EditOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { tradeDataApi } from '../services/api'
import dayjs from 'dayjs'

const { Option } = Select

interface TradeDataProps {
  readOnly?: boolean
}

const TradeData: React.FC<TradeDataProps> = ({ readOnly = false }) => {
  const queryClient = useQueryClient()
  const [filters, setFilters] = useState({
    year: undefined,
    hs_code: '',
    trade_partner: '',
    status: undefined,
    page: 1,
    page_size: 20,
  })

  // 获取数据列表
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['tradeData', filters],
    queryFn: () =>
      tradeDataApi.getList({
        ...filters,
        year: filters.year || undefined,
        status: filters.status || undefined,
      }).then(res => res.data),
  })

  // 确认数据
  const confirmMutation = useMutation({
    mutationFn: (id: number) => tradeDataApi.confirm(id),
    onSuccess: () => {
      message.success('确认成功')
      queryClient.invalidateQueries({ queryKey: ['tradeData'] })
    },
    onError: () => {
      message.error('确认失败')
    },
  })

  // 删除数据
  const deleteMutation = useMutation({
    mutationFn: (id: number) => tradeDataApi.delete(id),
    onSuccess: () => {
      message.success('删除成功')
      queryClient.invalidateQueries({ queryKey: ['tradeData'] })
    },
    onError: () => {
      message.error('删除失败')
    },
  })

  // 基础表格列定义
  const baseColumns: any[] = [
    {
      title: '年份',
      dataIndex: 'year',
      key: 'year',
      width: 80,
      sorter: true,
    },
    {
      title: 'HS编码',
      dataIndex: 'hs_code',
      key: 'hs_code',
      width: 120,
    },
    {
      title: 'HS描述',
      dataIndex: 'hs_description',
      key: 'hs_description',
      ellipsis: true,
    },
    {
      title: '贸易伙伴',
      dataIndex: 'trade_partner',
      key: 'trade_partner',
      width: 120,
    },
    {
      title: '出口数量',
      dataIndex: 'export_quantity',
      key: 'export_quantity',
      width: 120,
      render: (value: number) => value?.toLocaleString() || '-',
    },
    {
      title: '出口金额 (USD)',
      dataIndex: 'export_value_usd',
      key: 'export_value_usd',
      width: 150,
      render: (value: number) => `$${(value || 0).toLocaleString()}`,
    },
    {
      title: '单价',
      dataIndex: 'unit_value_usd',
      key: 'unit_value_usd',
      width: 100,
      render: (value: number) => value ? `$${value.toFixed(4)}` : '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Tag
          color={
            status === 'confirmed' ? 'success' :
            status === 'pending' ? 'warning' : 'error'
          }
        >
          {status === 'confirmed' ? '已确认' :
           status === 'pending' ? '待确认' : '已拒绝'}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => date ? dayjs(date).format('YYYY-MM-DD HH:mm') : '-',
    },
  ]

  // 管理操作列（仅非只读模式显示）
  const actionColumn = readOnly ? [] : [
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right' as const,
      render: (_: any, record: any) => (
        <Space size="small">
          {record.status === 'pending' && (
            <Button
              type="text"
              icon={<CheckCircleOutlined />}
              onClick={() => confirmMutation.mutate(record.id)}
              title="确认"
            />
          )}
          <Button
            type="text"
            icon={<EditOutlined />}
            title="编辑"
          />
          <Popconfirm
            title="确认删除"
            description="确定要删除这条数据吗？"
            onConfirm={() => deleteMutation.mutate(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              title="删除"
            />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const columns = [...baseColumns, ...actionColumn]

  const handleSearch = () => {
    setFilters(prev => ({ ...prev, page: 1 }))
    refetch()
  }

  const handleReset = () => {
    setFilters({
      year: undefined,
      hs_code: '',
      trade_partner: '',
      status: undefined,
      page: 1,
      page_size: 20,
    })
  }

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>
        {readOnly ? '外贸数据公开查询' : '外贸数据管理'}
      </h2>

      {/* 筛选区域 */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6} lg={4}>
            <Select
              placeholder="选择年份"
              style={{ width: '100%' }}
              allowClear
              value={filters.year}
              onChange={(value) => setFilters(prev => ({ ...prev, year: value }))}
            >
              <Option value={2022}>2022年</Option>
              <Option value={2023}>2023年</Option>
              <Option value={2024}>2024年</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={6} lg={4}>
            <Input
              placeholder="HS编码"
              value={filters.hs_code}
              onChange={(e) => setFilters(prev => ({ ...prev, hs_code: e.target.value }))}
              allowClear
            />
          </Col>
          <Col xs={24} sm={12} md={6} lg={4}>
            <Input
              placeholder="贸易伙伴"
              value={filters.trade_partner}
              onChange={(e) => setFilters(prev => ({ ...prev, trade_partner: e.target.value }))}
              allowClear
            />
          </Col>
          <Col xs={24} sm={12} md={6} lg={4}>
            <Select
              placeholder="状态"
              style={{ width: '100%' }}
              allowClear
              value={filters.status}
              onChange={(value) => setFilters(prev => ({ ...prev, status: value }))}
            >
              <Option value="pending">待确认</Option>
              <Option value="confirmed">已确认</Option>
              <Option value="rejected">已拒绝</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={6} lg={8}>
            <Space>
              <Button
                type="primary"
                icon={<SearchOutlined />}
                onClick={handleSearch}
              >
                查询
              </Button>
              <Button icon={<ReloadOutlined />} onClick={handleReset}>
                重置
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 数据表格 */}
      <Card>
        <Table
          columns={columns}
          dataSource={data?.items || []}
          rowKey="id"
          loading={isLoading}
          scroll={{ x: readOnly ? 1100 : 1200 }}
          pagination={{
            current: filters.page,
            pageSize: filters.page_size,
            total: data?.total || 0,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`,
            onChange: (page, pageSize) => {
              setFilters(prev => ({ ...prev, page, page_size: pageSize || 20 }))
            },
          }}
        />
      </Card>
    </div>
  )
}

export default TradeData

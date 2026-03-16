import React, { useState } from 'react'
import {
  Form,
  Input,
  Select,
  Button,
  Card,
  message,
  Row,
  Col,
  InputNumber,
  Space,
} from 'antd'
import { SaveOutlined, ReloadOutlined } from '@ant-design/icons'
import { useMutation } from '@tanstack/react-query'
import { tradeDataApi } from '../services/api'

const { Option } = Select
const { TextArea } = Input

const DataAdd: React.FC = () => {
  const [form] = Form.useForm()
  const [submitting, setSubmitting] = useState(false)

  // 提交数据
  const createMutation = useMutation({
    mutationFn: (values: any) => tradeDataApi.create(values),
    onSuccess: () => {
      message.success('数据添加成功')
      form.resetFields()
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '添加失败')
    },
  })

  const onFinish = async (values: any) => {
    setSubmitting(true)
    try {
      await createMutation.mutateAsync(values)
    } finally {
      setSubmitting(false)
    }
  }

  const onReset = () => {
    form.resetFields()
  }

  // 自动计算单价
  const calculateUnitValue = () => {
    const quantity = form.getFieldValue('export_quantity')
    const value = form.getFieldValue('export_value_usd')
    
    if (quantity && value && quantity > 0) {
      const unitValue = value / quantity
      form.setFieldsValue({ unit_value_usd: Number(unitValue.toFixed(4)) })
    }
  }

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>添加外贸数据</h2>

      <Card>
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          autoComplete="off"
        >
          <Row gutter={24}>
            <Col xs={24} sm={12} md={8}>
              <Form.Item
                label="年份"
                name="year"
                rules={[{ required: true, message: '请选择年份' }]}
              >
                <Select placeholder="选择年份">
                  <Option value={2022}>2022年</Option>
                  <Option value={2023}>2023年</Option>
                  <Option value={2024}>2024年</Option>
                  <Option value={2025}>2025年</Option>
                </Select>
              </Form.Item>
            </Col>

            <Col xs={24} sm={12} md={8}>
              <Form.Item
                label="HS编码"
                name="hs_code"
                rules={[{ required: true, message: '请输入HS编码' }]}
              >
                <Select placeholder="选择HS编码" showSearch>
                  <Option value="851762">851762 - 手机/通信终端设备</Option>
                  <Option value="851770">851770 - 电话机零件</Option>
                </Select>
              </Form.Item>
            </Col>

            <Col xs={24} sm={12} md={8}>
              <Form.Item
                label="贸易伙伴"
                name="trade_partner"
                rules={[{ required: true, message: '请输入贸易伙伴' }]}
              >
                <Select placeholder="选择贸易伙伴" showSearch allowClear>
                  <Option value="全球">全球</Option>
                  <Option value="美国">美国</Option>
                  <Option value="印度">印度</Option>
                  <Option value="越南">越南</Option>
                  <Option value="韩国">韩国</Option>
                  <Option value="日本">日本</Option>
                  <Option value="德国">德国</Option>
                  <Option value="英国">英国</Option>
                  <Option value="巴西">巴西</Option>
                  <Option value="俄罗斯">俄罗斯</Option>
                </Select>
              </Form.Item>
            </Col>

            <Col xs={24} sm={12} md={8}>
              <Form.Item
                label="出口数量"
                name="export_quantity"
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={0}
                  precision={2}
                  placeholder="请输入出口数量"
                  onChange={calculateUnitValue}
                />
              </Form.Item>
            </Col>

            <Col xs={24} sm={12} md={8}>
              <Form.Item
                label="数量单位"
                name="quantity_unit"
              >
                <Select placeholder="选择单位" allowClear>
                  <Option value="kg">千克 (kg)</Option>
                  <Option value="pcs">件 (pcs)</Option>
                  <Option value="set">套 (set)</Option>
                </Select>
              </Form.Item>
            </Col>

            <Col xs={24} sm={12} md={8}>
              <Form.Item
                label="出口金额 (USD)"
                name="export_value_usd"
                rules={[{ required: true, message: '请输入出口金额' }]}
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={0}
                  precision={2}
                  placeholder="请输入出口金额"
                  onChange={calculateUnitValue}
                />
              </Form.Item>
            </Col>

            <Col xs={24} sm={12} md={8}>
              <Form.Item
                label="单价值 (USD)"
                name="unit_value_usd"
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={0}
                  precision={4}
                  placeholder="自动计算"
                  disabled
                />
              </Form.Item>
            </Col>

            <Col xs={24} sm={12} md={8}>
              <Form.Item
                label="贸易方式"
                name="trade_mode"
              >
                <Select placeholder="选择贸易方式" allowClear>
                  <Option value="一般贸易">一般贸易</Option>
                  <Option value="加工贸易">加工贸易</Option>
                  <Option value="其他">其他</Option>
                </Select>
              </Form.Item>
            </Col>

            <Col xs={24} sm={12} md={8}>
              <Form.Item
                label="数据来源"
                name="data_source"
                initialValue="手动录入"
              >
                <Input placeholder="数据来源" disabled />
              </Form.Item>
            </Col>

            <Col xs={24}>
              <Form.Item
                label="备注"
                name="notes"
              >
                <TextArea
                  rows={3}
                  placeholder="请输入备注信息"
                  maxLength={500}
                  showCount
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item style={{ marginTop: 24, marginBottom: 0 }}>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                icon={<SaveOutlined />}
                loading={submitting}
                size="large"
              >
                保存数据
              </Button>
              <Button
                icon={<ReloadOutlined />}
                onClick={onReset}
                size="large"
              >
                重置
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}

export default DataAdd

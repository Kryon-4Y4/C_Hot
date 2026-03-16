# 外贸数据接口

## 获取数据列表

### GET /api/v1/trade-data

获取外贸数据列表，支持分页和筛选。

### 请求参数

#### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页条数，默认20，最大100 |
| year | integer | 否 | 年份筛选 |
| hs_code | string | 否 | HS编码筛选 |
| trade_partner | string | 否 | 贸易伙伴筛选 |
| status | string | 否 | 状态筛选 (pending/confirmed/rejected) |
| sort_by | string | 否 | 排序字段 |
| sort_order | string | 否 | 排序方式 (asc/desc) |

### 响应示例

```json
{
  "items": [
    {
      "id": 1,
      "year": 2024,
      "hs_code": "851762",
      "hs_description": "手机/通信终端设备",
      "trade_partner": "美国",
      "export_quantity": 1000000,
      "quantity_unit": "pcs",
      "export_value_usd": 50000000,
      "unit_value_usd": 50.0,
      "trade_mode": "一般贸易",
      "data_source": "UN Comtrade",
      "status": "confirmed",
      "created_at": "2024-01-15T10:30:00"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "pages": 5
}
```

---

## 添加数据

### POST /api/v1/trade-data

添加新的外贸数据记录。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| year | integer | 是 | 年份 |
| hs_code | string | 是 | HS编码 |
| hs_description | string | 否 | HS编码描述 |
| trade_partner | string | 是 | 贸易伙伴 |
| export_quantity | number | 否 | 出口数量 |
| quantity_unit | string | 否 | 数量单位 |
| export_value_usd | number | 是 | 出口金额（美元） |
| unit_value_usd | number | 否 | 单价值（美元） |
| trade_mode | string | 否 | 贸易方式 |
| notes | string | 否 | 备注 |

### 请求示例

```json
{
  "year": 2024,
  "hs_code": "851762",
  "hs_description": "手机/通信终端设备",
  "trade_partner": "美国",
  "export_quantity": 1000000,
  "quantity_unit": "pcs",
  "export_value_usd": 50000000,
  "trade_mode": "一般贸易"
}
```

### 响应示例

```json
{
  "id": 101,
  "year": 2024,
  "hs_code": "851762",
  "trade_partner": "美国",
  "export_value_usd": 50000000,
  "status": "pending",
  "created_at": "2024-01-15T10:30:00"
}
```

---

## 批量添加数据

### POST /api/v1/trade-data/bulk

批量添加外贸数据（需要管理员权限）。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| - | array | 是 | TradeDataCreate对象数组 |

### 响应示例

```json
{
  "message": "成功添加 10 条数据"
}
```

---

## 获取单条数据

### GET /api/v1/trade-data/{id}

根据ID获取单条数据详情。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | integer | 是 | 数据ID |

### 响应示例

```json
{
  "id": 1,
  "year": 2024,
  "hs_code": "851762",
  "trade_partner": "美国",
  "export_value_usd": 50000000,
  "status": "confirmed",
  "created_at": "2024-01-15T10:30:00"
}
```

---

## 更新数据

### PUT /api/v1/trade-data/{id}

更新指定ID的数据。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | integer | 是 | 数据ID |

### 请求参数

与添加数据相同，所有字段可选。

### 响应示例

```json
{
  "id": 1,
  "year": 2024,
  "hs_code": "851762",
  "trade_partner": "美国",
  "export_value_usd": 55000000,
  "status": "confirmed",
  "updated_at": "2024-01-16T14:20:00"
}
```

---

## 删除数据

### DELETE /api/v1/trade-data/{id}

删除指定ID的数据（需要管理员权限）。

### 响应示例

```json
{
  "message": "数据删除成功"
}
```

---

## 确认数据

### POST /api/v1/trade-data/{id}/confirm

将pending状态的数据转为confirmed状态。

### 响应示例

```json
{
  "id": 1,
  "status": "confirmed",
  "confirmed_by": 1,
  "confirmed_at": "2024-01-16T14:20:00"
}
```

---

## 获取统计数据

### GET /api/v1/trade-data/statistics/overview

获取统计数据概览。

### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| year | integer | 否 | 指定年份，不指定则统计所有年份 |

### 响应示例

```json
{
  "total_records": 150,
  "total_value_usd": 1250000000,
  "hs_statistics": [
    {
      "hs_code": "851762",
      "total_value": 1000000000,
      "count": 100
    },
    {
      "hs_code": "851770",
      "total_value": 250000000,
      "count": 50
    }
  ],
  "top_partners": [
    {
      "partner": "美国",
      "total_value": 500000000,
      "count": 30
    },
    {
      "partner": "印度",
      "total_value": 300000000,
      "count": 25
    }
  ]
}
```

---

## 按年份统计

### GET /api/v1/trade-data/statistics/by-year

获取按年份的统计数据。

### 响应示例

```json
[
  {
    "year": 2022,
    "total_value_usd": 400000000,
    "record_count": 50
  },
  {
    "year": 2023,
    "total_value_usd": 420000000,
    "record_count": 50
  },
  {
    "year": 2024,
    "total_value_usd": 430000000,
    "record_count": 50
  }
]
```

# 爬虫管理接口

## 获取爬虫脚本列表

### GET /api/v1/crawler/scripts

获取爬虫脚本列表。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页条数，默认20 |
| is_active | boolean | 否 | 是否启用筛选 |

### 响应示例

```json
[
  {
    "id": 1,
    "name": "UN Comtrade 爬虫",
    "description": "从UN Comtrade获取中国手机维修配件出口数据",
    "code": "...",
    "hs_codes": "851762,851770",
    "periods": "2022,2023,2024",
    "is_active": true,
    "auto_run": false,
    "version": "1.0.0",
    "created_at": "2024-01-15T10:30:00"
  }
]
```

---

## 创建爬虫脚本

### POST /api/v1/crawler/scripts

创建新的爬虫脚本（需要管理员权限）。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 脚本名称（唯一） |
| description | string | 否 | 脚本描述 |
| code | string | 是 | Python代码 |
| hs_codes | string | 否 | HS编码列表（逗号分隔） |
| periods | string | 否 | 查询年份列表（逗号分隔） |
| partners | string | 否 | 贸易伙伴JSON配置 |
| is_active | boolean | 否 | 是否启用，默认true |
| auto_run | boolean | 否 | 是否自动运行，默认false |
| cron_expression | string | 否 | 定时表达式 |
| version | string | 否 | 版本号，默认"1.0.0" |

---

## 获取爬虫脚本详情

### GET /api/v1/crawler/scripts/{id}

根据ID获取爬虫脚本详情。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | integer | 是 | 脚本ID |

---

## 更新爬虫脚本

### PUT /api/v1/crawler/scripts/{id}

更新指定ID的爬虫脚本（需要管理员权限）。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | integer | 是 | 脚本ID |

### 请求参数

与创建脚本相同，所有字段可选。

---

## 删除爬虫脚本

### DELETE /api/v1/crawler/scripts/{id}

删除指定ID的爬虫脚本（需要管理员权限）。

### 响应示例

```json
{
  "message": "脚本删除成功"
}
```

---

## 获取爬虫任务列表

### GET /api/v1/crawler/tasks

获取爬虫任务列表。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页条数，默认20 |
| script_id | integer | 否 | 脚本ID筛选 |
| status | string | 否 | 状态筛选 (pending/running/success/failed/cancelled) |

### 响应示例

```json
[
  {
    "id": 1,
    "script_id": 1,
    "script_name": "UN Comtrade 爬虫",
    "status": "success",
    "started_at": "2024-01-15T10:30:00",
    "completed_at": "2024-01-15T10:35:00",
    "duration_seconds": 300,
    "total_records": 50,
    "new_records": 10,
    "updated_records": 40,
    "trigger_type": "manual",
    "created_at": "2024-01-15T10:30:00"
  }
]
```

---

## 获取爬虫任务详情

### GET /api/v1/crawler/tasks/{id}

根据ID获取爬虫任务详情。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | integer | 是 | 任务ID |

### 响应示例

```json
{
  "id": 1,
  "script_id": 1,
  "script_name": "UN Comtrade 爬虫",
  "status": "success",
  "started_at": "2024-01-15T10:30:00",
  "completed_at": "2024-01-15T10:35:00",
  "duration_seconds": 300,
  "total_records": 50,
  "new_records": 10,
  "updated_records": 40,
  "error_count": 0,
  "logs": "[2024-01-15 10:30:00] 开始执行爬虫...",
  "error_message": null,
  "triggered_by": 1,
  "trigger_type": "manual",
  "created_at": "2024-01-15T10:30:00"
}
```

---

## 触发爬虫任务

### POST /api/v1/crawler/trigger

手动触发爬虫任务（需要管理员权限）。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| script_id | integer | 是 | 脚本ID |
| params | object | 否 | 执行参数 |

### 响应示例

```json
{
  "task_id": 2,
  "message": "爬虫任务已创建，任务ID: 2"
}
```

---

## 取消爬虫任务

### POST /api/v1/crawler/tasks/{id}/cancel

取消待执行或运行中的爬虫任务（需要管理员权限）。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | integer | 是 | 任务ID |

### 响应示例

```json
{
  "message": "任务已取消"
}
```

### 错误响应

| 状态码 | 说明 |
|--------|------|
| 400 | 只能取消待执行或运行中的任务 |
| 404 | 任务不存在 |

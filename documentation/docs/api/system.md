# 系统接口

## 健康检查

### GET /api/v1/system/health

系统健康检查。

### 响应示例

```json
{
  "status": "healthy",
  "timestamp": "2024-01-16T14:20:00",
  "version": "1.0.0"
}
```

---

## 获取系统统计

### GET /api/v1/system/stats

获取系统统计信息（需要管理员权限）。

### 响应示例

```json
{
  "database": {
    "trade_data_count": 150,
    "user_count": 5,
    "crawler_task_count": 20
  },
  "redis": {
    "connected": true,
    "used_memory_human": "2.5M",
    "connected_clients": 5,
    "total_commands_processed": 10000
  },
  "system": {
    "platform": "Linux-5.15.0",
    "python_version": "3.11.0",
    "cpu_percent": 15.5,
    "memory": {
      "total": 8589934592,
      "available": 4294967296,
      "percent": 50.0
    },
    "disk": {
      "total": 107374182400,
      "used": 53687091200,
      "free": 53687091200,
      "percent": 50.0
    }
  },
  "timestamp": "2024-01-16T14:20:00"
}
```

---

## 获取系统信息

### GET /api/v1/system/info

获取系统基本信息。

### 响应示例

```json
{
  "app_name": "手机维修配件外贸数据管理系统",
  "app_version": "1.0.0",
  "debug": false
}
```

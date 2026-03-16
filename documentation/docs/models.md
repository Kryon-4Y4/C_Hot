# 数据模型

## 用户模型 (User)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 主键 |
| username | string | 用户名（唯一） |
| email | string | 邮箱（唯一） |
| hashed_password | string | 密码哈希 |
| full_name | string | 全名 |
| role | enum | 角色（admin/user/viewer） |
| is_active | boolean | 是否激活 |
| is_superuser | boolean | 是否超级用户 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |
| last_login | datetime | 最后登录时间 |

## 外贸数据模型 (TradeData)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 主键 |
| year | integer | 年份 |
| hs_code | string | HS编码 |
| hs_description | string | HS编码描述 |
| trade_partner | string | 贸易伙伴 |
| export_quantity | decimal | 出口数量 |
| quantity_unit | string | 数量单位 |
| export_value_usd | decimal | 出口金额（美元） |
| unit_value_usd | decimal | 单价值（美元） |
| trade_mode | string | 贸易方式 |
| data_source | string | 数据来源 |
| status | string | 状态（pending/confirmed/rejected） |
| confirmed_by | integer | 确认用户ID |
| confirmed_at | datetime | 确认时间 |
| notes | text | 备注 |
| crawled_at | datetime | 抓取时间 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

## 爬虫脚本模型 (CrawlerScript)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 主键 |
| name | string | 脚本名称（唯一） |
| description | text | 脚本描述 |
| code | text | Python代码 |
| hs_codes | string | HS编码列表（逗号分隔） |
| periods | string | 查询年份列表（逗号分隔） |
| partners | text | 贸易伙伴JSON配置 |
| is_active | boolean | 是否启用 |
| auto_run | boolean | 是否自动运行 |
| cron_expression | string | 定时表达式 |
| version | string | 版本号 |
| created_by | integer | 创建用户ID |
| updated_by | integer | 更新用户ID |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

## 爬虫任务模型 (CrawlerTask)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 主键 |
| script_id | integer | 脚本ID |
| script_name | string | 脚本名称 |
| status | string | 任务状态（pending/running/success/failed/cancelled） |
| started_at | datetime | 开始时间 |
| completed_at | datetime | 完成时间 |
| duration_seconds | decimal | 执行时长（秒） |
| total_records | integer | 获取记录数 |
| new_records | integer | 新增记录数 |
| updated_records | integer | 更新记录数 |
| error_count | integer | 错误数 |
| logs | text | 执行日志 |
| error_message | text | 错误信息 |
| triggered_by | integer | 触发用户ID |
| trigger_type | string | 触发类型（manual/auto/retry） |
| created_at | datetime | 创建时间 |

## 审计日志模型 (AuditLog)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 主键 |
| action | string | 操作类型 |
| resource_type | string | 资源类型 |
| resource_id | string | 资源ID |
| user_id | integer | 用户ID |
| username | string | 用户名 |
| ip_address | string | IP地址 |
| user_agent | string | 用户代理 |
| old_values | json | 变更前值 |
| new_values | json | 变更后值 |
| description | text | 操作描述 |
| created_at | datetime | 创建时间 |

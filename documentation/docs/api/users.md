# 用户管理接口

## 获取用户列表

### GET /api/v1/users

获取用户列表（需要管理员权限）。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页条数，默认20 |
| role | string | 否 | 角色筛选 (admin/user/viewer) |
| is_active | boolean | 否 | 是否激活筛选 |

### 响应示例

```json
[
  {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "full_name": "系统管理员",
    "role": "admin",
    "is_active": true,
    "is_superuser": true,
    "created_at": "2024-01-15T10:30:00",
    "last_login": "2024-01-16T14:20:00"
  }
]
```

---

## 创建用户

### POST /api/v1/users

创建新用户（需要管理员权限）。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名（3-50字符） |
| email | string | 是 | 邮箱 |
| password | string | 是 | 密码（至少8位） |
| full_name | string | 否 | 全名 |
| role | string | 否 | 角色，默认"user" |
| is_active | boolean | 否 | 是否激活，默认true |

### 响应示例

```json
{
  "id": 2,
  "username": "operator",
  "email": "operator@example.com",
  "full_name": "操作员",
  "role": "user",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2024-01-16T14:20:00"
}
```

### 错误响应

| 状态码 | 说明 |
|--------|------|
| 400 | 用户名或邮箱已存在 |

---

## 获取当前用户信息

### GET /api/v1/users/me

获取当前登录用户的详细信息。

### 响应示例

```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "full_name": "系统管理员",
  "role": "admin",
  "is_active": true,
  "is_superuser": true,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-16T14:20:00",
  "last_login": "2024-01-16T14:20:00"
}
```

---

## 获取指定用户信息

### GET /api/v1/users/{id}

根据ID获取用户信息（需要管理员权限）。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | integer | 是 | 用户ID |

---

## 更新用户

### PUT /api/v1/users/{id}

更新用户信息（需要管理员权限）。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | integer | 是 | 用户ID |

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| email | string | 否 | 邮箱 |
| full_name | string | 否 | 全名 |
| role | string | 否 | 角色 |
| is_active | boolean | 否 | 是否激活 |
| password | string | 否 | 新密码（至少8位） |

---

## 删除用户

### DELETE /api/v1/users/{id}

删除用户（需要管理员权限）。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | integer | 是 | 用户ID |

### 错误响应

| 状态码 | 说明 |
|--------|------|
| 403 | 不能删除超级管理员 |
| 404 | 用户不存在 |

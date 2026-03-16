# 认证接口

## 用户登录

### POST /api/v1/auth/login

用户登录，获取访问令牌。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |

### 请求示例

```json
{
  "username": "admin",
  "password": "admin123"
}
```

### 响应示例

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "full_name": "系统管理员",
    "role": "admin"
  }
}
```

### 错误响应

| 状态码 | 说明 |
|--------|------|
| 401 | 用户名或密码错误 |
| 403 | 用户已被禁用 |

---

## 刷新令牌

### POST /api/v1/auth/refresh

使用刷新令牌获取新的访问令牌。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| refresh_token | string | 是 | 刷新令牌 |

### 响应示例

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

## 用户登出

### POST /api/v1/auth/logout

用户登出（客户端需要清除令牌）。

### 响应示例

```json
{
  "message": "登出成功"
}
```

---

## 获取当前用户信息

### GET /api/v1/auth/me

获取当前登录用户的信息。

### 请求头

| 参数 | 必填 | 说明 |
|------|------|------|
| Authorization | 是 | Bearer Token |

### 响应示例

```json
{
  "username": "admin",
  "user_id": 1,
  "role": "admin"
}
```

---

## 修改密码

### POST /api/v1/auth/change-password

修改当前用户密码。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| old_password | string | 是 | 原密码 |
| new_password | string | 是 | 新密码（至少8位） |

### 响应示例

```json
{
  "message": "密码修改成功"
}
```

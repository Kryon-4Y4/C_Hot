# 快速开始

## 环境准备

### 系统要求

- Docker >= 20.0
- Docker Compose >= 2.0
- 内存 >= 4GB
- 磁盘 >= 10GB

### 安装Docker

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com | sh

# MacOS
brew install docker docker-compose

# Windows
# 下载Docker Desktop并安装
```

## 启动系统

### 1. 克隆代码

```bash
git clone <repository-url>
cd phone-parts-trade-system
```

### 2. 配置环境变量

```bash
cp .env.example .env

# 编辑.env文件，设置必要的配置
vim .env
```

### 3. 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 4. 初始化数据

```bash
# 创建管理员账户
docker-compose exec admin python -m app.main create-admin
```

## 访问服务

服务启动后，可以通过以下地址访问：

| 服务 | 地址 | 说明 |
|------|------|------|
| 用户前台 | http://localhost:3000 | React应用 |
| API文档 | http://localhost:8000/docs | Swagger UI |
| API ReDoc | http://localhost:8000/redoc | ReDoc文档 |
| 管理后台 | http://localhost:5000 | Flask Admin |
| 运维后台 | http://localhost:8001 | Ops API |
| 文档站 | http://localhost:8080 | 本文档 |

### 默认账户

- 用户名: `admin`
- 密码: `admin123`

## API使用示例

### 1. 获取访问令牌

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

响应：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 2. 查询外贸数据

```bash
curl -X GET "http://localhost:8000/api/v1/trade-data?page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. 添加外贸数据

```bash
curl -X POST http://localhost:8000/api/v1/trade-data \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "year": 2024,
    "hs_code": "851762",
    "trade_partner": "美国",
    "export_value_usd": 1000000
  }'
```

## 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v
```

## 故障排除

### 服务无法启动

```bash
# 检查端口占用
netstat -tlnp | grep 8000

# 查看详细日志
docker-compose logs backend
docker-compose logs postgres
```

### 数据库连接失败

```bash
# 检查数据库状态
docker-compose exec postgres pg_isready

# 重置数据库
docker-compose down -v
docker-compose up -d postgres
```

### 爬虫任务不执行

```bash
# 检查调度服务日志
docker-compose logs scheduler

# 检查Redis队列
docker-compose exec redis redis-cli llen crawler_tasks
```

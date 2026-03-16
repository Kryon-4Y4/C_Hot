# 部署指南

## 环境要求

### 最低配置

- CPU: 2核
- 内存: 4GB
- 磁盘: 20GB
- 网络: 可访问互联网

### 推荐配置

- CPU: 4核+
- 内存: 8GB+
- 磁盘: 50GB+ SSD
- 网络: 100Mbps+

## Docker部署

### 1. 安装Docker

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# 验证安装
docker --version
docker-compose --version
```

### 2. 配置环境变量

```bash
cp .env.example .env

# 编辑配置文件
vim .env
```

关键配置项：

```bash
# 数据库密码（必须修改）
DB_PASSWORD=your_secure_password

# 安全密钥（必须修改，建议32位随机字符串）
SECRET_KEY=your-super-secret-key

# 调试模式（生产环境设为false）
DEBUG=false
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
# 等待数据库就绪
docker-compose exec postgres pg_isready

# 创建管理员账户
docker-compose exec admin python -m app.main create-admin
```

## 生产环境优化

### 数据库优化

```sql
-- 创建索引
CREATE INDEX CONCURRENTLY idx_trade_data_year_hs ON trade_data(year, hs_code);
CREATE INDEX CONCURRENTLY idx_trade_data_partner ON trade_data(trade_partner);

-- 定期清理旧数据
DELETE FROM crawler_tasks 
WHERE created_at < NOW() - INTERVAL '90 days' 
AND status IN ('success', 'failed', 'cancelled');
```

### Nginx配置

```nginx
upstream backend {
    server backend:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # 前端静态文件
    location / {
        root /var/www/frontend;
        try_files $uri $uri/ /index.html;
    }
    
    # API代理
    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 备份策略

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# 数据库备份
docker-compose exec -T postgres pg_dump -U postgres phone_parts_db > $BACKUP_DIR/db.sql

# 文件备份
tar czf $BACKUP_DIR/files.tar.gz ./data

# 上传到远程存储
aws s3 cp $BACKUP_DIR s3://your-backup-bucket/ --recursive

# 清理旧备份
find /backup -type d -mtime +30 -exec rm -rf {} \;
```

## 监控告警

### 使用Prometheus + Grafana

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  grafana_data:
```

### 关键指标

- API响应时间
- 数据库连接数
- 爬虫任务成功率
- 系统资源使用率

## 故障恢复

### 数据库恢复

```bash
# 停止服务
docker-compose stop backend

# 恢复数据库
docker-compose exec -T postgres psql -U postgres < backup.sql

# 重启服务
docker-compose start backend
```

### 服务重启

```bash
# 重启单个服务
docker-compose restart backend

# 重启所有服务
docker-compose restart

# 强制重新构建
docker-compose up -d --build
```

# 常见问题

## 部署相关

### Q: 如何修改数据库密码？

A: 修改 `.env` 文件中的 `DB_PASSWORD`，然后重新创建容器：

```bash
docker-compose down -v  # 注意：这会删除数据卷
docker-compose up -d
```

如果已有数据，需要先备份再恢复。

### Q: 如何升级系统？

A: 

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build

# 执行数据库迁移（如有）
docker-compose exec backend alembic upgrade head
```

### Q: 如何查看容器日志？

A:

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看指定服务日志
docker-compose logs -f backend

# 查看最近100行
docker-compose logs --tail=100 backend
```

## 使用相关

### Q: 忘记管理员密码怎么办？

A: 重置密码：

```bash
docker-compose exec postgres psql -U postgres -d phone_parts_db -c "
UPDATE users SET hashed_password = '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiAYMyzJ/I1m' WHERE username = 'admin';
"
```

重置后密码为 `admin123`。

### Q: 爬虫任务失败怎么办？

A:

1. 查看任务日志：
```bash
docker-compose logs scheduler | grep "任务ID"
```

2. 检查UN Comtrade API可用性

3. 手动重试任务

### Q: 如何添加新的HS编码？

A:

1. 登录管理后台
2. 进入"爬虫脚本"页面
3. 编辑对应脚本
4. 修改 `hs_codes` 字段
5. 保存并重新触发爬虫

## 性能相关

### Q: 数据量大了查询变慢怎么办？

A:

1. 添加数据库索引：
```sql
CREATE INDEX CONCURRENTLY idx_year_partner ON trade_data(year, trade_partner);
```

2. 增加缓存

3. 优化查询条件

4. 考虑分表或分区

### Q: 爬虫采集速度太慢怎么办？

A:

1. 调整请求间隔（在爬虫脚本中修改）

2. 使用代理池

3. 增加并发worker数量

4. 申请UN Comtrade API订阅密钥

## 安全相关

### Q: 如何启用HTTPS？

A: 在 `docker-compose.yml` 前添加Nginx反向代理，配置SSL证书。

或使用Traefik等自动HTTPS解决方案。

### Q: 如何限制IP访问？

A: 在Nginx配置中添加：

```nginx
location / {
    allow 192.168.1.0/24;
    deny all;
    # ...
}
```

## 开发相关

### Q: 如何本地开发调试？

A: 各组件支持独立开发：

```bash
# 后端API
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# 前端
cd frontend
npm install
npm run dev

# 调度服务
cd scheduler
pip install -r requirements.txt
celery -A app.worker worker --loglevel=info
```

### Q: 如何添加新的API接口？

A:

1. 在 `backend/app/api/` 添加路由
2. 在 `backend/app/schemas/` 添加模型
3. 在 `backend/app/services/` 添加业务逻辑
4. 更新API文档

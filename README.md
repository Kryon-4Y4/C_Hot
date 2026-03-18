# 手机维修配件外贸数据管理系统

  一个完整的手机维修配件外贸出货数据管理平台，支持数据采集、任务调度、权限管理和数据可视化分析。

## 系统架构

### 架构图

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#e1f5fe', 'primaryTextColor': '#01579b', 'primaryBorderColor': '#0288d1', 'lineColor': '#0288d1', 'secondaryColor': '#fff3e0', 'tertiaryColor': '#e8f5e9'}}}%%

graph TB
    subgraph 用户层[用户访问层]
        PORTAL[用户门户<br/>user-portal:3000<br/>🔍 只读查询]
        ADMIN[管理控制台<br/>admin-console:5000<br/>✏️ 管理员操作]
        OPS[运维中心<br/>ops-center:8001]
        DOCS[文档站点<br/>documentation:8080]
    end

    subgraph 网关层[API 网关层]
        APIGW[API Gateway<br/>api-gateway:8000<br/>🔐 统一认证/路由]
    end

    subgraph 服务层[业务服务层]
        SCHEDULER[任务调度器<br/>task-scheduler<br/>Celery]
        CRAWLER[爬虫核心<br/>crawler<br/>UN Comtrade API]
    end

    subgraph 数据层[数据基础设施层]
        DATALAYER[data-layer<br/>共享数据模型<br/>SQLAlchemy]
        POSTGRES[(PostgreSQL<br/>数据库)]
        REDIS[(Redis<br/>缓存/队列)]
    end

    %% ========== 用户门户：只读查询 ==========
    PORTAL -->|🔍 只读 REST API| APIGW
    APIGW -->|查询已确认数据| DATALAYER
    
    %% ========== 管理员操作流 ==========
    %% 1. 脚本管理（CRUD脚本配置）
    ADMIN -->|✏️ 脚本管理 API| APIGW
    APIGW -->|保存脚本配置| DATALAYER
    DATALAYER -->|存储脚本| POSTGRES
    
    %% 2. 触发爬虫任务（仅管理员）
    ADMIN -->|▶️ 触发任务 API| APIGW
    APIGW -->|创建任务| SCHEDULER
    
    %% 3. 查看报表（管理员）
    ADMIN -->|📊 统计报表 API| APIGW
    APIGW -->|查询数据| DATALAYER
    
    %% 4. 数据确认（管理员审核）
    ADMIN -->|✅ 确认数据 API| APIGW
    APIGW -->|更新状态| DATALAYER
    
    %% ========== 爬虫任务执行流 ==========
    SCHEDULER -.->|1. 推送任务| REDIS
    SCHEDULER -.->|2. 消费任务| REDIS
    SCHEDULER -->|3. 读取脚本配置| DATALAYER
    DATALAYER -->|返回脚本| POSTGRES
    SCHEDULER -->|4. 触发| CRAWLER
    CRAWLER -->|5. 抓取数据| EXTERNAL[🌐 UN Comtrade<br/>外站数据源]
    EXTERNAL -->|返回原始数据| CRAWLER
    CRAWLER -->|6. 写入待确认数据| DATALAYER
    DATALAYER -->|存储待确认| POSTGRES
    
    %% ========== 运维监控 ==========
    OPS -->|监控API| APIGW
    
    %% ========== 数据层内部 ==========
    DATALAYER -.->|缓存| REDIS

    %% 样式
    classDef frontend fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef gateway fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef service fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef data fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    classDef storage fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef external fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    
    class PORTAL,ADMIN,OPS,DOCS frontend
    class APIGW gateway
    class SCHEDULER,CRAWLER service
    class DATALAYER data
    class POSTGRES,REDIS storage
    class EXTERNAL external
```

### 分层说明

| 层级 | 组件 | 职责 | 数据权限 | 访问控制 |
|------|------|------|---------|---------|
| **用户访问层** | user-portal<br>admin-console<br>ops-center<br>documentation | 用户门户（React）<br>管理后台（Flask-Admin）<br>运维监控<br>项目文档 | 只读查询<br>完整CRUD + 任务触发<br>监控查询<br>静态文档 | JWT认证<br>JWT认证<br>Internal<br>- |
| **API 网关层** | api-gateway | 统一入口、JWT认证、权限校验、路由<br>任务调度API（仅管理员） | 权限控制代理 | 所有请求必经 |
| **业务服务层** | task-scheduler<br>crawler | 异步任务调度（Celery）<br>UN Comtrade数据抓取 | 读取脚本配置<br>写入待确认数据 | 仅内部服务调用<br>无外网暴露 |
| **数据基础设施层** | data-layer<br>PostgreSQL<br>Redis | 共享ORM模型<br>主数据库<br>任务队列/缓存 | 数据持久化 | 内网访问 |


### 核心流程

```mermaid
sequenceDiagram
    actor User as 普通用户
    actor Admin as 管理员
    participant Portal as 用户门户
    participant AdminConsole as 管理控制台
    participant APIGW as API Gateway
    participant Scheduler as 任务调度器
    participant Crawler as 爬虫核心
    participant External as UN Comtrade
    participant DataLayer as data-layer
    participant DB as PostgreSQL
    participant Redis as Redis

    %% ========== 流程1：普通用户查询已确认数据（只读） ==========
    User->>Portal: 1. 查询外贸数据
    Portal->>APIGW: 2. GET /api/v1/trade-data
    Note over APIGW: JWT认证 + 只读权限
    APIGW->>DataLayer: 3. 查询已确认数据
    DataLayer->>DB: 4. SELECT status='confirmed'
    DB-->>DataLayer: 5. 返回数据
    DataLayer-->>APIGW: 6. 数据结果
    APIGW-->>Portal: 7. JSON Response
    Portal-->>User: 8. 展示数据（无编辑功能）

    %% ========== 流程2：管理员管理爬虫脚本 ==========
    Admin->>AdminConsole: A. 创建/编辑爬虫脚本
    AdminConsole->>APIGW: B. POST/PUT /api/v1/admin/crawler-scripts
    Note over APIGW: JWT认证 + 管理员权限
    APIGW->>DataLayer: C. 保存脚本配置
    DataLayer->>DB: D. INSERT/UPDATE crawler_scripts
    DB-->>DataLayer: E. 保存成功
    DataLayer-->>APIGW: F. 返回结果
    APIGW-->>AdminConsole: G. 脚本配置完成
    AdminConsole-->>Admin: H. 确认保存

    %% ========== 流程3：管理员触发爬虫任务（核心流程） ==========
    Admin->>AdminConsole: I. 选择脚本并触发任务
    AdminConsole->>APIGW: J. POST /api/v1/crawler/trigger
    Note over APIGW: 仅管理员可调用的API
    APIGW->>Scheduler: K. 创建异步任务
    Scheduler->>DB: L. 记录任务状态（pending）
    
    %% 任务调度执行
    Scheduler->>Redis: M. 推送任务到队列
    Scheduler->>Redis: N. 消费任务
    Scheduler->>DataLayer: O. 读取脚本配置
    DataLayer->>DB: P. SELECT crawler_scripts
    DB-->>DataLayer: Q. 返回脚本参数
    DataLayer-->>Scheduler: R. 脚本配置
    
    Scheduler->>Crawler: S. 执行爬取（脚本参数）
    Crawler->>External: T. HTTP请求抓取数据
    External-->>Crawler: U. 返回原始JSON数据
    
    Crawler->>DataLayer: V. 解析并写入待确认数据
    DataLayer->>DB: W. INSERT trade_data status='pending'
    DB-->>DataLayer: X. 写入成功
    DataLayer-->>Scheduler: Y. 任务完成
    Scheduler->>DB: Z. 更新任务状态（completed）
    Scheduler-->>APIGW: AA. 任务执行结果
    APIGW-->>AdminConsole: AB. 任务完成通知
    AdminConsole-->>Admin: AC. 显示任务成功

    %% ========== 流程4：管理员查看报表并确认数据 ==========
    Admin->>AdminConsole: AD. 查看数据统计报表
    AdminConsole->>APIGW: AE. GET /api/v1/admin/reports
    APIGW->>DataLayer: AF. 查询统计数据
    DataLayer->>DB: AG. 聚合查询
    DB-->>DataLayer: AH. 返回统计结果
    DataLayer-->>APIGW: AI. 报表数据
    APIGW-->>AdminConsole: AJ. JSON Response
    AdminConsole-->>Admin: AK. 展示图表（年份/HS编码/贸易伙伴）
    
    Admin->>AdminConsole: AL. 查看并确认待确认数据
    AdminConsole->>APIGW: AM. POST /api/v1/admin/trade-data/confirm
    APIGW->>DataLayer: AN. 更新数据状态
    DataLayer->>DB: AO. UPDATE status='confirmed'
    DB-->>DataLayer: AP. 更新成功
    DataLayer-->>APIGW: AQ. 确认结果
    APIGW-->>AdminConsole: AR. 操作成功
    AdminConsole-->>Admin: AS. 数据已确认（用户可见）
```

## 目录结构

```
phone-parts-trade-system/
├── docker-compose.yml          # Docker编排配置
├── README.md                   # 项目文档
├── .env.example               # 环境变量模板
│
├── crawler/                   # 爬虫核心
│   ├── mobile_phone_spare_parts_crawler.py
│   └── 手机维修配件外贸出货数据.csv
│
├── data-layer/                # 数据层 (共享组件) ⭐
│   ├── data_layer/            # Python包
│   │   ├── __init__.py
│   │   ├── database.py        # 数据库连接
│   │   └── models/            # 共享数据模型
│   │       ├── user.py        # 用户模型（bcrypt加密）
│   │       ├── trade_data.py  # 外贸数据
│   │       ├── crawler_script.py  # 爬虫脚本
│   │       ├── crawler_task.py    # 爬虫任务
│   │       └── audit_log.py       # 审计日志
│   ├── init.sql               # 数据库初始化
│   ├── setup.py               # Python包配置
│   ├── Dockerfile             # 基础镜像
│   └── requirements.txt
│
├── api-gateway/               # API网关 (FastAPI)
│   ├── app/
│   │   ├── api/              # 路由层
│   │   ├── core/             # 核心配置（JWT认证）
│   │   ├── schemas/          # 数据校验
│   │   ├── services/         # 业务逻辑
│   │   ├── database.py       # (从data-layer导入)
│   │   └── main.py
│   ├── Dockerfile            # 基于data-layer构建
│   └── requirements.txt
│
├── task-scheduler/            # 任务调度 (Celery)
│   ├── app/
│   │   ├── crawler_adapter.py # UN Comtrade API适配器
│   │   ├── tasks.py           # Celery任务定义
│   │   └── worker.py          # Worker配置
│   ├── Dockerfile            # 基于data-layer构建
│   └── requirements.txt
│
├── user-portal/               # 用户门户 (React + Ant Design)
│   ├── src/
│   │   ├── pages/            # 页面组件
│   │   │   └── TradeData.tsx # 外贸数据查询（只读）
│   │   ├── components/       # 公共组件
│   │   └── App.tsx           # 路由配置
│   ├── Dockerfile
│   └── package.json
│
├── admin-console/             # 管理控制台 (Flask-Admin)
│   ├── app/
│   │   ├── main.py           # 主应用（含仪表盘）
│   │   └── templates/        # 报表模板
│   │       └── admin/
│   │           └── report_dashboard.html
│   ├── Dockerfile            # 基于data-layer构建
│   └── requirements.txt
│
├── ops-center/                # 运维中心 (FastAPI)
│   ├── app/
│   │   └── main.py
│   ├── Dockerfile            # 基于data-layer构建
│   └── requirements.txt
│
└── documentation/             # 文档站点 (MkDocs)
    ├── docs/                 # 文档源文件
    ├── mkdocs.yml           # 站点配置
    └── Dockerfile
```

## 组件说明

### data-layer/ - 数据层 ⭐核心组件

**设计哲学**: 统一数据访问，避免代码重复

```python
# 使用示例
from data_layer import TradeData, get_db_session

# 任意服务都可以这样访问数据
with get_db_session() as db:
    data = db.query(TradeData).filter_by(year=2024).all()
```

**包含内容**:
- 数据库连接池 (`database.py`)
- 5个核心模型 (`models/`)
- 基础CRUD操作
- **bcrypt密码加密**（替代passlib，解决72字节限制）

**优势**:
- ✅ 模型定义一处维护
- ✅ 强制数据一致性
- ✅ 作为Docker基础镜像复用

### 其他组件

| 组件 | 技术栈 | 基于data-layer | 端口 | 职责 | 认证方式 |
|------|--------|----------------|------|------|---------|
| api-gateway | FastAPI | ✅ | 8000 | 统一API入口、权限校验 | JWT Token |
| task-scheduler | Celery + Beat | ✅ | - | 异步任务调度 | 内部调用 |
| admin-console | Flask-Admin | ❌ | 5000 | 管理后台UI（调用API Gateway） | Session + JWT |
| ops-center | FastAPI | ✅ | 8001 | 运维监控API | Internal |
| user-portal | React 18 | ❌ | 3000 | 用户门户UI（调用API Gateway） | JWT Token |
| documentation | MkDocs Material | ❌ | 8080 | 静态文档站点 | - |

## 核心功能特性

### 1. 外贸数据管理
- **数据审核流程**: 
  - 爬虫抓取的数据标记为「待确认」
  - 管理员审核后确认，数据变为「已确认」
  - 仅「已确认」数据对用户可见
- **多维度查询**: 按年份、HS编码、贸易伙伴、状态筛选
- **数据导出**: 支持CSV格式导出
- **权限分级**: 
  - 管理员：查看所有数据 + 确认操作
  - 普通用户：仅查看已确认数据

### 2. 爬虫任务调度（仅管理员）
- **脚本配置管理**: 管理员在 Admin Console 配置爬虫参数（HS编码、年份、贸易伙伴等）
- **手动触发执行**: 仅管理员可触发爬虫任务，防止滥用
- **异步任务队列**: Celery + Redis 处理后台抓取任务
- **实时状态跟踪**: 任务状态、进度、日志实时展示
- **数据源**: UN Comtrade API（手机配件HS编码：851762、851770等）

### 3. 数据统计报表（管理员）
- **集成仪表盘**: 嵌入Flask-Admin框架的统计视图
- **可视化图表**: Chart.js绘制年份趋势、HS编码分布、数据来源
- **关键指标**: 总记录数、待确认/已确认数量、出口总额
- **Top排名**: 主要贸易伙伴排行榜（按出口金额）

### 4. 安全与审计
- **统一API入口**: 所有前端应用通过 API Gateway 访问数据
- **分层权限控制**: 
  - API Gateway: JWT Token认证 + 权限校验
  - Admin Console: Session认证（管理后台登录）
- **bcrypt加密**: 安全密码存储（替代passlib）
- **审计日志**: 记录所有数据变更和操作
- **操作追踪**: 谁在什么时间做了什么操作

## 快速开始

### 环境要求

- Docker >= 20.0
- Docker Compose >= 2.0
- 内存 >= 4GB
- 磁盘 >= 10GB

### 启动服务

```bash
# 1. 配置环境变量
cp .env.example .env

# 2. 构建基础镜像（先构建data-layer）
docker-compose build data-layer

# 3. 启动所有服务
docker-compose up -d

# 4. 等待数据库初始化完成（约30秒）
docker-compose logs -f data-layer

# 5. 创建管理员账户（首次运行）
docker-compose exec admin-console python -c "
from data_layer import get_db_session, User
from data_layer.models import UserRole
import bcrypt

db = get_db_session()
if not db.query(User).filter_by(username='admin').first():
    hashed = bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt())
    admin = User(
        username='admin',
        email='admin@example.com',
        hashed_password=hashed.decode(),
        role=UserRole.ADMIN,
        is_active=True
    )
    db.add(admin)
    db.commit()
    print('管理员创建成功')
db.close()
"
```

### 访问服务

| 服务 | 地址 | 说明 | 默认凭证 |
|------|------|------|---------|
| 用户门户 | http://localhost:3000 | React前端（只读） | - |
| API文档 | http://localhost:8000/docs | Swagger UI | JWT Token |
| 管理控制台 | http://localhost:5000 | Flask Admin | admin / admin123 |
| 运维中心 | http://localhost:8001 | 监控API | - |
| 文档站点 | http://localhost:8080 | 项目文档 | - |

### 使用流程示例

#### 1. 管理员配置爬虫脚本
```
登录 Admin Console → 爬虫脚本管理 → 
调用 API Gateway（管理员权限）→ 
创建/编辑脚本（配置HS编码、抓取年份等）→ 
脚本配置保存到数据库
```

#### 2. 管理员触发数据采集（核心流程）
```
Admin Console → 选择脚本 → 触发运行 → 
调用 API Gateway（仅管理员可调用）→ 
Task Scheduler 创建异步任务 → 加入 Redis 队列 → 
Celery Worker 读取脚本配置 → 执行 Crawler → 
抓取 UN Comtrade 数据 → 解析并写入待确认数据 → 
任务完成，通知管理员
```

#### 3. 管理员审核确认数据
```
Admin Console → 查看待确认数据 → 
数据质量检查 → 批量/单条确认 → 
调用 API Gateway 更新状态（pending → confirmed）→ 
数据正式对用户可见
```

#### 4. 管理员查看统计报表
```
Admin Console → 数据报表 → 
调用 API Gateway 获取统计数据 → 
查看可视化图表（年份趋势、HS编码分布、贸易伙伴排行）→ 
分析数据 → 导出报表
```

#### 5. 普通用户查询数据（只读）
```
打开 User Portal → 筛选条件（年份/HS编码/贸易伙伴/状态）→ 
调用 API Gateway（JWT认证，仅查询已确认数据）→ 
返回查询结果 → 查看数据列表（无编辑功能）→ 导出CSV
```

## 开发指南

### 添加新模型

1. 在 `data-layer/data_layer/models/` 创建模型
2. 导出到 `data_layer/models/__init__.py`
3. 重建镜像: `docker-compose build data-layer`
4. 重建依赖服务: `docker-compose up -d --build`

### 本地开发

```bash
# 安装数据层
pip install -e ./data-layer

# 启动API网关
cd api-gateway && uvicorn app.main:app --reload --port 8000

# 启动Celery Worker（新终端）
cd task-scheduler
celery -A app.worker worker --loglevel=info -Q default,crawler

# 启动Celery Beat（定时任务，新终端）
celery -A app.worker beat --loglevel=info
```

### 调试技巧

```bash
# 查看服务日志
docker-compose logs -f admin-console
docker-compose logs -f task-scheduler

# 进入容器调试
docker-compose exec admin-console bash
docker-compose exec postgres psql -U postgres -d phone_parts

# 查看Celery队列
docker-compose exec redis redis-cli LLEN celery
```

## 生产部署建议

### 1. 安全加固
- 修改所有默认密码
- 启用HTTPS（配置Nginx反向代理）
- 配置CORS白名单
- 设置JWT过期时间（建议1小时）

### 2. 性能优化
- PostgreSQL添加连接池（PgBouncer）
- Redis配置持久化
- Celery Worker根据CPU核心数扩展
- 启用API Gateway的GZip压缩

### 3. 监控告警
- 配置Prometheus + Grafana监控
- 设置Celery任务失败告警
- 监控数据库连接数和慢查询
- 配置日志聚合（ELK或Loki）

## 常见问题

### Q: Celery任务不执行？
A: 检查Worker是否监听`crawler`队列：
```bash
docker-compose exec task-scheduler celery -A app.worker inspect active
```

### Q: 用户门户显示空白？
A: 检查API Gateway是否可访问，以及CORS配置是否正确。

### Q: 数据库迁移失败？
A: 使用`docker-compose down -v`清除卷后重新启动，或手动执行ALTER TABLE。

### Q: 如何重置管理员密码？
A: 进入admin-console容器执行Python脚本重新哈希密码。

## 技术栈版本

| 组件 | 版本 |
|------|------|
| Python | 3.11 |
| FastAPI | 0.104+ |
| Flask-Admin | 1.6+ |
| Celery | 5.3+ |
| PostgreSQL | 15 |
| Redis | 7 |
| React | 18 |
| Node.js | 20 |

## 许可证

MIT License

---

**维护者**: Matrix Agent  
**最后更新**: 2026-03-17

"""
管理控制台 - Flask Admin（带登录保护）
"""
import os
import csv
import io
import json
import redis
from flask import Flask, redirect, url_for, request, session, render_template_string, flash, jsonify, Response
from flask_admin import Admin, AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_admin.base import MenuLink
from sqlalchemy.orm import scoped_session, sessionmaker
from functools import wraps
from datetime import datetime, timedelta

# 从 data-layer 导入
from data_layer import Base, engine
from data_layer.models import User, CrawlerScript, CrawlerTask, AuditLog, TradeData

# 创建应用
app = Flask(__name__)

# 配置
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'admin-secret-key-change-in-production')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'

# 数据库会话
Session = scoped_session(sessionmaker(bind=engine))
db_session = Session()

# API Gateway 地址
API_GATEWAY_URL = os.getenv('API_GATEWAY_URL', 'http://api-gateway:8000')

# Redis 连接
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# 登录页面模板
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>管理控制台登录</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; }
        .login-card { max-width: 400px; margin: 0 auto; background: white; border-radius: 16px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); padding: 40px; }
        .login-icon { width: 80px; height: 80px; border-radius: 50%; background: linear-gradient(135deg, #1890ff 0%, #36cfc9 100%); display: flex; align-items: center; justify-content: center; margin: 0 auto 24px; color: white; font-size: 36px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="login-card">
            <div class="login-icon">🔐</div>
            <h3 class="text-center mb-4">管理控制台登录</h3>
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ 'danger' if category == 'error' else category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            <form method="POST" action="/login">
                <div class="mb-3">
                    <label class="form-label">用户名</label>
                    <input type="text" name="username" class="form-control" required placeholder="admin">
                </div>
                <div class="mb-3">
                    <label class="form-label">密码</label>
                    <input type="password" name="password" class="form-control" required placeholder="admin123">
                </div>
                <button type="submit" class="btn btn-primary w-100" style="height: 48px; border-radius: 8px;">登录</button>
            </form>
            <p class="text-center text-muted mt-3" style="font-size: 12px;">默认账号: admin / admin123</p>
        </div>
    </div>
</body>
</html>
'''


def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


# 自定义 ModelView，添加登录保护
class SecureModelView(ModelView):
    """带登录保护的模型视图"""
    
    def is_accessible(self):
        return session.get('admin_logged_in') is True
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))


class UserAdmin(SecureModelView):
    column_list = ['id', 'username', 'email', 'full_name', 'role', 'is_active', 'email_subscribed', 'created_at']
    column_searchable_list = ['username', 'email', 'full_name']
    column_filters = ['role', 'is_active', 'email_subscribed', 'created_at']
    form_columns = ['username', 'email', 'full_name', 'role', 'is_active', 'is_superuser', 'email_subscribed']
    can_create = True
    can_edit = True
    can_delete = True
    
    def on_model_change(self, form, model, is_created):
        """创建用户时设置默认密码"""
        if is_created:
            from app.core.security import get_password_hash
            model.hashed_password = get_password_hash('user123')  # 默认密码


class CrawlerScriptAdmin(SecureModelView):
    column_list = ['id', 'name', 'version', 'is_active', 'auto_run', 'cron_expression', 'created_at', 'actions']
    column_searchable_list = ['name', 'description']
    column_filters = ['is_active', 'auto_run', 'created_at']
    form_columns = [
        'name', 'description', 'code', 'hs_codes', 'periods', 
        'partners', 'is_active', 'auto_run', 'cron_expression', 'version'
    ]
    form_widget_args = {
        'code': {
            'rows': 20,
            'style': 'font-family: monospace;'
        },
        'partners': {
            'rows': 5,
            'placeholder': 'JSON格式，例如：{"840": "美国", "356": "印度"}'
        }
    }
    
    # 详情页显示代码
    column_details_list = ['id', 'name', 'description', 'code', 'hs_codes', 'periods', 
                          'partners', 'is_active', 'auto_run', 'cron_expression', 
                          'version', 'created_at', 'updated_at']
    
    # 格式化名称列，添加代码查看链接
    def _name_formatter(view, context, model, name):
        return f'<a href="/admin/crawler/script/{model.id}/code" title="查看Python代码">🐍 {model.name}</a>'
    
    # 格式化操作列
    def _actions_formatter(view, context, model, name):
        run_btn = f'<a href="/admin/crawler/run/{model.id}" class="btn btn-primary btn-sm" onclick="return confirm(\'确定运行此脚本?\')">▶ 运行</a>'
        code_btn = f'<a href="/admin/crawler/script/{model.id}/code" class="btn btn-info btn-sm">查看代码</a>'
        return f'{run_btn} {code_btn}'
    
    column_formatters = {
        'name': _name_formatter,
        'actions': _actions_formatter
    }


class CrawlerTaskAdmin(SecureModelView):
    column_list = ['id', 'script_name', 'status', 'started_at', 'completed_at', 'total_records', 'new_records', 'actions']
    column_searchable_list = ['script_name']
    column_filters = ['status', 'trigger_type', 'created_at']
    can_create = False
    can_edit = False
    can_delete = False
    column_default_sort = ('created_at', True)
    
    # 详情页显示完整信息
    column_details_list = ['id', 'script_name', 'status', 'started_at', 'completed_at', 
                          'duration_seconds', 'total_records', 'new_records', 'updated_records',
                          'error_count', 'error_message', 'logs', 'trigger_type', 'created_at']
    
    # 格式化状态列
    def _status_formatter(view, context, model, name):
        badge_class = {
            'success': 'bg-success',
            'failed': 'bg-danger', 
            'running': 'bg-primary',
            'pending': 'bg-warning'
        }.get(model.status, 'bg-secondary')
        return f'<span class="badge {badge_class}">{model.status}</span>'
    
    # 格式化操作列
    def _actions_formatter(view, context, model, name):
        logs_btn = f'<a href="/admin/crawler/task/{model.id}/logs" class="btn btn-info btn-sm">日志</a>'
        if model.status == 'success':
            export_btn = f'<a href="/admin/crawler/task/{model.id}/export" class="btn btn-success btn-sm">导出CSV</a>'
            return f'{logs_btn} {export_btn}'
        return logs_btn
    
    column_formatters = {
        'status': _status_formatter,
        'actions': _actions_formatter
    }


class AuditLogAdmin(SecureModelView):
    """审计日志视图"""
    column_list = ['id', 'action', 'resource_type', 'username', 'ip_address', 'created_at']
    column_searchable_list = ['username', 'action', 'resource_type']
    column_filters = ['action', 'resource_type', 'created_at']
    can_create = False
    can_edit = False
    can_delete = False
    column_default_sort = ('created_at', True)
    
    column_details_list = [
        'id', 'action', 'resource_type', 'resource_id', 
        'user_id', 'username', 'ip_address', 'user_agent',
        'old_values', 'new_values', 'description', 'created_at'
    ]


class TradeDataAdmin(SecureModelView):
    """外贸数据管理视图 - 支持CRUD"""
    column_list = ['id', 'year', 'hs_code', 'hs_description', 'trade_partner', 
                   'export_value_usd', 'export_quantity', 'status', 'data_source', 'created_at']
    column_searchable_list = ['hs_code', 'hs_description', 'trade_partner', 'data_source']
    column_filters = ['year', 'hs_code', 'status', 'data_source', 'created_at']
    column_default_sort = ('created_at', True)
    
    # 可编辑列
    form_columns = [
        'year', 'hs_code', 'hs_description', 'trade_partner',
        'export_quantity', 'quantity_unit', 'export_value_usd', 'unit_value_usd',
        'trade_mode', 'data_source', 'notes', 'status'
    ]
    
    # 列格式化
    column_formatters = {
        'export_value_usd': lambda v, c, m, n: f'${m.export_value_usd:,.2f}' if m.export_value_usd else '-',
        'status': lambda v, c, m, n: f'<span class="badge {"bg-success" if m.status=="confirmed" else "bg-warning"}">{m.status}</span>'
    }
    
    # 批量操作
    can_export = True
    export_types = ['csv']
    
    def on_model_change(self, form, model, is_created):
        """保存数据时的处理"""
        if is_created:
            model.status = 'confirmed'  # 管理员创建的数据直接确认
            model.data_source = model.data_source or 'manual'
        # 记录审计日志
        try:
            from flask import session as flask_session
            audit_log = AuditLog(
                action='create_trade_data' if is_created else 'update_trade_data',
                resource_type='trade_data',
                resource_id=str(model.id),
                username=flask_session.get('admin_username', 'admin'),
                ip_address=request.remote_addr,
                description=f'{"创建" if is_created else "更新"}外贸数据: {model.hs_code} - {model.trade_partner}'
            )
            db_session.add(audit_log)
            db_session.commit()
        except:
            db_session.rollback()
    
    def on_model_delete(self, model):
        """删除数据时的处理"""
        try:
            from flask import session as flask_session
            audit_log = AuditLog(
                action='delete_trade_data',
                resource_type='trade_data',
                resource_id=str(model.id),
                username=flask_session.get('admin_username', 'admin'),
                ip_address=request.remote_addr,
                description=f'删除外贸数据: {model.hs_code} - {model.trade_partner}'
            )
            db_session.add(audit_log)
            db_session.commit()
        except:
            db_session.rollback()


# 自定义首页视图
class HomeView(AdminIndexView):
    """自定义 Admin 首页视图"""
    
    @expose('/')
    def index(self):
        if not session.get('admin_logged_in'):
            return redirect(url_for('login', next=request.url))
        return redirect(url_for('admin_home'))
    
    def is_accessible(self):
        return session.get('admin_logged_in') is True
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))


# 创建Admin
admin = Admin(
    app, 
    name='管理控制台', 
    template_mode='bootstrap4',
    index_view=HomeView()
)

# 添加视图
admin.add_view(UserAdmin(User, db_session, name='用户管理', endpoint='usermanager'))
admin.add_view(CrawlerScriptAdmin(CrawlerScript, db_session, name='爬虫脚本', endpoint='crawlerscript'))
admin.add_view(CrawlerTaskAdmin(CrawlerTask, db_session, name='爬虫任务'))
admin.add_view(TradeDataAdmin(TradeData, db_session, name='外贸数据', endpoint='tradedata'))
admin.add_view(AuditLogAdmin(AuditLog, db_session, name='操作日志'))
admin.add_view(ReportDashboardView(name='数据报表', endpoint='reports', url='/reports/dashboard'))

# 添加菜单链接
admin.add_link(MenuLink(name='📊 系统统计', url='/admin/home', category=''))
admin.add_link(MenuLink(name='🚪 退出登录', url='/logout', category=''))


# ========== 自定义路由 ==========

# 首页仪表盘 - 带统计图表
@app.route('/admin/home')
@login_required
def admin_home():
    """管理控制台首页 - 统计仪表盘"""
    from sqlalchemy import func
    
    # 用户统计
    user_stats = {
        'total': db_session.query(User).count(),
        'active': db_session.query(User).filter_by(is_active=True).count(),
        'admin': db_session.query(User).filter_by(role='admin').count(),
        'subscribed': db_session.query(User).filter_by(email_subscribed=True).count(),
        'new_today': db_session.query(User).filter(
            func.date(User.created_at) == func.current_date()
        ).count()
    }
    
    # 获取最近30天用户增长数据
    thirty_days_ago = datetime.now() - timedelta(days=30)
    user_growth = db_session.query(
        func.date(User.created_at).label('date'),
        func.count(User.id).label('count')
    ).filter(
        User.created_at >= thirty_days_ago
    ).group_by(
        func.date(User.created_at)
    ).order_by('date').all()
    
    # 填充缺失日期
    dates = []
    counts = []
    date_map = {str(d): c for d, c in user_growth}
    for i in range(30):
        date = (datetime.now() - timedelta(days=29-i)).strftime('%Y-%m-%d')
        dates.append(date[5:])  # 只显示 MM-DD
        counts.append(date_map.get(date, 0))
    
    # 爬虫任务统计
    task_stats = db_session.query(
        CrawlerTask.status,
        func.count(CrawlerTask.id)
    ).group_by(CrawlerTask.status).all()
    task_counts = {s: c for s, c in task_stats}
    
    # 最近7天任务统计
    week_ago = datetime.now() - timedelta(days=7)
    recent_tasks = db_session.query(CrawlerTask).filter(
        CrawlerTask.created_at >= week_ago
    ).count()
    
    # 爬虫脚本列表（用于显示运行按钮）
    scripts = db_session.query(CrawlerScript).filter_by(is_active=True).all()
    
    # 最近任务
    recent_task_list = db_session.query(CrawlerTask).order_by(
        CrawlerTask.created_at.desc()
    ).limit(10).all()
    
    # 最近10条操作日志
    recent_logs = db_session.query(AuditLog).order_by(
        AuditLog.created_at.desc()
    ).limit(10).all()
    
    # 外贸数据统计
    trade_stats = {
        'total': db_session.query(TradeData).count(),
        'confirmed': db_session.query(TradeData).filter_by(status='confirmed').count(),
        'pending': db_session.query(TradeData).filter_by(status='pending').count(),
    }
    
    home_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>管理控制台 - 首页</title>
        <meta charset="utf-8">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            .stats-card { border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.1); padding: 20px; margin-bottom: 24px; background: white; }
            .stat-item { text-align: center; padding: 16px; }
            .stat-value { font-size: 28px; font-weight: bold; color: #1890ff; }
            .stat-label { color: #666; margin-top: 8px; font-size: 14px; }
            .chart-container { position: relative; height: 300px; }
            .script-card { border: 1px solid #e8e8e8; border-radius: 8px; padding: 16px; margin-bottom: 12px; }
            .script-name { font-weight: bold; color: #1890ff; }
            .script-meta { font-size: 12px; color: #999; margin-top: 4px; }
            .navbar-brand { font-weight: bold; }
            .section-title { font-size: 18px; font-weight: bold; margin-bottom: 16px; color: #333; }
            .log-table { font-size: 13px; }
            .log-table td { padding: 8px; }
            .badge-pending { background-color: #faad14; }
            .badge-running { background-color: #1890ff; }
            .badge-success { background-color: #52c41a; }
            .badge-failed { background-color: #f5222d; }
            .task-item { padding: 8px 12px; border-left: 3px solid #1890ff; background: #f6ffed; margin-bottom: 8px; border-radius: 0 4px 4px 0; }
            .task-pending { border-left-color: #faad14; background: #fffbe6; }
            .task-running { border-left-color: #1890ff; background: #e6f7ff; }
            .task-success { border-left-color: #52c41a; background: #f6ffed; }
            .task-failed { border-left-color: #f5222d; background: #fff1f0; }
        </style>
    </head>
    <body style="background: #f0f2f5;">
        <nav class="navbar navbar-dark" style="background: linear-gradient(135deg, #1890ff 0%, #36cfc9 100%);">
            <div class="container-fluid">
                <span class="navbar-brand">📊 管理控制台</span>
                <div>
                    <a href="/admin/" class="btn btn-light btn-sm">详细管理</a>
                    <a href="/admin/export/trade-data" class="btn btn-success btn-sm ms-2">📥 导出数据</a>
                    <a href="/logout" class="btn btn-outline-light btn-sm ms-2">退出</a>
                </div>
            </div>
        </nav>
        
        <div class="container-fluid mt-4" style="padding: 0 24px 24px;">
            <!-- 顶部统计卡片 -->
            <div class="row">
                <div class="col-md-2">
                    <div class="stats-card">
                        <div class="stat-item">
                            <div class="stat-value">{{ user_stats.total }}</div>
                            <div class="stat-label">总用户数</div>
                        </div>
                    </div>
                </div>
                <div class="col-md-2">
                    <div class="stats-card">
                        <div class="stat-item">
                            <div class="stat-value" style="color: #52c41a;">{{ user_stats.active }}</div>
                            <div class="stat-label">活跃用户</div>
                        </div>
                    </div>
                </div>
                <div class="col-md-2">
                    <div class="stats-card">
                        <div class="stat-item">
                            <div class="stat-value" style="color: #722ed1;">{{ user_stats.new_today }}</div>
                            <div class="stat-label">今日新增</div>
                        </div>
                    </div>
                </div>
                <div class="col-md-2">
                    <div class="stats-card">
                        <div class="stat-item">
                            <div class="stat-value" style="color: #fa8c16;">{{ trade_stats.total }}</div>
                            <div class="stat-label">数据记录</div>
                        </div>
                    </div>
                </div>
                <div class="col-md-2">
                    <div class="stats-card">
                        <div class="stat-item">
                            <div class="stat-value" style="color: #13c2c2;">{{ task_counts.get('pending', 0) }}</div>
                            <div class="stat-label">待执行任务</div>
                        </div>
                    </div>
                </div>
                <div class="col-md-2">
                    <div class="stats-card">
                        <div class="stat-item">
                            <div class="stat-value" style="color: #eb2f96;">{{ task_counts.get('running', 0) }}</div>
                            <div class="stat-label">运行中</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- 图表区域 -->
            <div class="row">
                <div class="col-md-8">
                    <div class="stats-card">
                        <div class="section-title">📈 用户增长趋势（近30天）</div>
                        <div class="chart-container">
                            <canvas id="userGrowthChart"></canvas>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stats-card">
                        <div class="section-title">🥧 任务状态分布</div>
                        <div class="chart-container">
                            <canvas id="taskStatusChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- 爬虫控制和任务列表 -->
            <div class="row">
                <div class="col-md-6">
                    <div class="stats-card">
                        <div class="section-title">🕷️ 爬虫脚本控制</div>
                        <p class="text-muted mb-3">点击运行按钮立即执行爬虫任务</p>
                        {% for script in scripts %}
                        <div class="script-card">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <div class="script-name">{{ script.name }}</div>
                                    <div class="script-meta">
                                        {% if script.auto_run %}
                                        <span class="badge bg-info">自动运行</span>
                                        {% endif %}
                                        {% if script.cron_expression %}
                                        <span class="badge bg-secondary">{{ script.cron_expression }}</span>
                                        {% endif %}
                                        <span class="ms-2">版本: {{ script.version }}</span>
                                    </div>
                                </div>
                                <a href="/admin/crawler/run/{{ script.id }}" class="btn btn-primary btn-sm">
                                    <i class="fas fa-play"></i> 运行
                                </a>
                            </div>
                        </div>
                        {% endfor %}
                        <div class="mt-3">
                            <a href="/admin/crawlerscript/" class="btn btn-outline-primary btn-sm">
                                <i class="fas fa-cog"></i> 管理脚本 & 定时设置
                            </a>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="stats-card">
                        <div class="section-title">📋 最近任务</div>
                        {% for task in recent_task_list %}
                        <div class="task-item task-{{ task.status }}">
                            <div class="d-flex justify-content-between">
                                <span><strong>{{ task.script_name }}</strong></span>
                                <span class="badge badge-{{ task.status }}">{{ task.status }}</span>
                            </div>
                            <div class="text-muted mt-1" style="font-size: 12px;">
                                {{ task.created_at.strftime('%m-%d %H:%M') if task.created_at else '-' }}
                                {% if task.total_records > 0 %}
                                | 获取 {{ task.total_records }} 条记录
                                {% endif %}
                            </div>
                        </div>
                        {% endfor %}
                        <div class="mt-3 text-end">
                            <a href="/admin/crawlertask/" class="btn btn-outline-secondary btn-sm">查看全部</a>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- 操作日志 -->
            <div class="stats-card">
                <div class="section-title">📝 最近操作日志</div>
                <table class="table table-hover log-table">
                    <thead>
                        <tr>
                            <th>时间</th>
                            <th>操作</th>
                            <th>资源类型</th>
                            <th>用户</th>
                            <th>IP地址</th>
                            <th>描述</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for log in recent_logs %}
                        <tr>
                            <td>{{ log.created_at.strftime('%m-%d %H:%M') if log.created_at else '-' }}</td>
                            <td><span class="badge bg-secondary">{{ log.action }}</span></td>
                            <td>{{ log.resource_type }}</td>
                            <td>{{ log.username or '访客' }}</td>
                            <td>{{ log.ip_address or '-' }}</td>
                            <td>{{ log.description or '-' }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        
        <script>
            // 用户增长图表
            const ctx1 = document.getElementById('userGrowthChart').getContext('2d');
            new Chart(ctx1, {
                type: 'line',
                data: {
                    labels: {{ dates | tojson }},
                    datasets: [{
                        label: '新增用户',
                        data: {{ counts | tojson }},
                        borderColor: '#1890ff',
                        backgroundColor: 'rgba(24, 144, 255, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: { beginAtZero: true, ticks: { stepSize: 1 } }
                    }
                }
            });
            
            // 任务状态饼图
            const ctx2 = document.getElementById('taskStatusChart').getContext('2d');
            new Chart(ctx2, {
                type: 'doughnut',
                data: {
                    labels: ['待执行', '执行中', '成功', '失败'],
                    datasets: [{
                        data: [
                            {{ task_counts.get('pending', 0) }},
                            {{ task_counts.get('running', 0) }},
                            {{ task_counts.get('success', 0) }},
                            {{ task_counts.get('failed', 0) }}
                        ],
                        backgroundColor: ['#faad14', '#1890ff', '#52c41a', '#f5222d']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom' }
                    }
                }
            });
        </script>
    </body>
    </html>
    '''
    
    return render_template_string(
        home_template,
        user_stats=user_stats,
        dates=dates,
        counts=counts,
        task_counts=task_counts,
        recent_tasks=recent_tasks,
        scripts=scripts,
        recent_task_list=recent_task_list,
        recent_logs=recent_logs,
        trade_stats=trade_stats
    )


# 爬虫任务调度
@app.route('/admin/crawler/run/<int:script_id>', methods=['GET', 'POST'])
@login_required
def run_crawler(script_id):
    """立即执行爬虫脚本"""
    try:
        script = db_session.query(CrawlerScript).get(script_id)
        if not script:
            flash('脚本不存在', 'error')
            return redirect(url_for('admin_home'))
        
        # 创建任务记录
        task = CrawlerTask(
            script_id=script_id,
            script_name=script.name,
            status='pending',
            trigger_type='manual'
        )
        db_session.add(task)
        db_session.commit()
        
        # 发送任务到 Redis 队列
        task_message = {
            "task_id": task.id,
            "script_id": script.id,
            "script_name": script.name,
            "script_code": script.code,
            "hs_codes": script.hs_codes,
            "periods": script.periods,
            "partners": script.partners,
            "triggered_by": session.get('admin_user_id'),
            "params": {}
        }
        redis_client.lpush("crawler_tasks", json.dumps(task_message))
        
        # 记录审计日志
        audit_log = AuditLog(
            action='trigger_crawler',
            resource_type='crawler_script',
            resource_id=str(script_id),
            username=session.get('admin_username', 'admin'),
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else '',
            description=f'手动触发爬虫脚本: {script.name}, 任务ID: {task.id}'
        )
        db_session.add(audit_log)
        db_session.commit()
        
        flash(f'爬虫任务已创建并提交执行: {script.name} (任务ID: {task.id})', 'success')
    except Exception as e:
        db_session.rollback()
        flash(f'触发爬虫失败: {str(e)}', 'error')
    
    return redirect(url_for('admin_home'))


# 查看爬虫任务日志
@app.route('/admin/crawler/task/<int:task_id>/logs')
@login_required
def view_crawler_logs(task_id):
    """查看爬虫任务日志"""
    task = db_session.query(CrawlerTask).get(task_id)
    if not task:
        flash('任务不存在', 'error')
        return redirect(url_for('crawlertask.index_view'))
    
    logs_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>任务日志 - {{ task.script_name }}</title>
        <meta charset="utf-8">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background: #f5f5f5; padding: 20px; }
            .log-container { background: #1e1e1e; color: #d4d4d4; padding: 20px; border-radius: 8px; 
                           font-family: 'Consolas', 'Monaco', monospace; font-size: 13px; 
                           max-height: 80vh; overflow-y: auto; white-space: pre-wrap; }
            .log-header { margin-bottom: 20px; }
            .status-badge { font-size: 14px; padding: 6px 12px; border-radius: 4px; }
            .timestamp { color: #6c757d; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="log-header">
                <h4>📋 任务日志: {{ task.script_name }}</h4>
                <p>
                    <span class="badge status-badge 
                        {% if task.status == 'success' %}bg-success
                        {% elif task.status == 'failed' %}bg-danger
                        {% elif task.status == 'running' %}bg-primary
                        {% else %}bg-warning{% endif %}">
                        {{ task.status }}
                    </span>
                    <span class="ms-3">任务ID: {{ task.id }}</span>
                    <span class="ms-3">创建时间: {{ task.created_at }}</span>
                    {% if task.duration_seconds %}
                    <span class="ms-3">耗时: {{ task.duration_seconds }}秒</span>
                    {% endif %}
                </p>
                <a href="/admin/crawlertask/" class="btn btn-secondary btn-sm">← 返回任务列表</a>
                {% if task.status == 'success' %}
                <a href="/admin/crawler/task/{{ task.id }}/export" class="btn btn-success btn-sm">📥 导出CSV</a>
                {% endif %}
            </div>
            
            <div class="log-container">
{% if task.logs %}{{ task.logs }}{% else %}暂无日志记录...{% endif %}
            </div>
            
            {% if task.error_message %}
            <div class="alert alert-danger mt-3">
                <strong>错误信息:</strong><br>
                {{ task.error_message }}
            </div>
            {% endif %}
        </div>
    </body>
    </html>
    '''
    
    return render_template_string(logs_template, task=task)


# 导出爬虫任务数据
@app.route('/admin/crawler/task/<int:task_id>/export')
@login_required
def export_crawler_task_data(task_id):
    """导出爬虫任务爬取的数据（该任务创建时间之后的数据）"""
    try:
        task = db_session.query(CrawlerTask).get(task_id)
        if not task:
            flash('任务不存在', 'error')
            return redirect(url_for('crawlertask.index_view'))
        
        # 查询该任务执行期间创建的数据
        # 使用 crawled_at 字段来识别爬虫数据
        from sqlalchemy import text
        
        if task.status != 'success':
            flash('只能导出已成功完成的任务数据', 'error')
            return redirect(url_for('crawlertask.index_view'))
        
        # 查询数据（该任务创建时间之后的数据）
        query = db_session.query(TradeData).filter(
            TradeData.data_source == 'UN Comtrade',
            TradeData.created_at >= task.created_at
        )
        
        # 如果是刚完成的任务，限制在任务完成时间之前
        if task.completed_at:
            query = query.filter(TradeData.created_at <= task.completed_at)
        
        data = query.order_by(TradeData.created_at.desc()).limit(task.total_records * 2).all()
        
        # 生成CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        writer.writerow([
            'ID', '年份', 'HS编码', 'HS描述', '贸易伙伴', '出口数量', 
            '数量单位', '出口金额(USD)', '单价值(USD)', '贸易方式', 
            '数据来源', '爬取时间', '创建时间'
        ])
        
        # 写入数据
        for item in data:
            writer.writerow([
                item.id,
                item.year,
                item.hs_code,
                item.hs_description or '',
                item.trade_partner,
                item.export_quantity or '',
                item.quantity_unit or '',
                item.export_value_usd or '',
                item.unit_value_usd or '',
                item.trade_mode or '',
                item.data_source or '',
                item.crawled_at.strftime('%Y-%m-%d %H:%M:%S') if item.crawled_at else '',
                item.created_at.strftime('%Y-%m-%d %H:%M:%S') if item.created_at else ''
            ])
        
        # 记录审计日志
        audit_log = AuditLog(
            action='export_crawler_data',
            resource_type='crawler_task',
            resource_id=str(task_id),
            username=session.get('admin_username', 'admin'),
            ip_address=request.remote_addr,
            description=f'导出爬虫任务数据: {task.script_name}, 任务ID: {task_id}, 记录数: {len(data)}'
        )
        db_session.add(audit_log)
        db_session.commit()
        
        # 返回CSV文件
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=crawler_task_{task_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            }
        )
    except Exception as e:
        flash(f'导出失败: {str(e)}', 'error')
        return redirect(url_for('crawlertask.index_view'))


# 查看爬虫脚本代码
@app.route('/admin/crawler/script/<int:script_id>/code')
@login_required
def view_crawler_code(script_id):
    """查看爬虫脚本代码"""
    script = db_session.query(CrawlerScript).get(script_id)
    if not script:
        flash('脚本不存在', 'error')
        return redirect(url_for('crawlerscript.index_view'))
    
    code_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>脚本代码 - {{ script.name }}</title>
        <meta charset="utf-8">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background: #f5f5f5; padding: 20px; }
            .code-container { background: #1e1e1e; color: #d4d4d4; padding: 20px; border-radius: 8px; 
                            font-family: 'Consolas', 'Monaco', monospace; font-size: 13px; 
                            max-height: 80vh; overflow-y: auto; white-space: pre; }
            .code-header { margin-bottom: 20px; }
            .btn-run { float: right; }
            .meta-info { background: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="code-header">
                <h4>🐍 脚本代码: {{ script.name }}</h4>
                <a href="/admin/crawlerscript/" class="btn btn-secondary btn-sm">← 返回脚本列表</a>
                <a href="/admin/crawler/run/{{ script.id }}" class="btn btn-primary btn-sm" onclick="return confirm('确定要运行此脚本吗？')">
                    ▶ 运行脚本
                </a>
            </div>
            
            <div class="meta-info">
                <div class="row">
                    <div class="col-md-3"><strong>版本:</strong> {{ script.version }}</div>
                    <div class="col-md-3"><strong>状态:</strong> 
                        <span class="badge {% if script.is_active %}bg-success{% else %}bg-secondary{% endif %}">
                            {% if script.is_active %}启用{% else %}禁用{% endif %}
                        </span>
                    </div>
                    <div class="col-md-3"><strong>自动运行:</strong> 
                        <span class="badge {% if script.auto_run %}bg-info{% else %}bg-secondary{% endif %}">
                            {% if script.auto_run %}是{% else %}否{% endif %}
                        </span>
                    </div>
                    <div class="col-md-3"><strong>定时:</strong> {{ script.cron_expression or '-' }}</div>
                </div>
                <div class="row mt-2">
                    <div class="col-md-4"><strong>HS编码:</strong> {{ script.hs_codes or '默认' }}</div>
                    <div class="col-md-4"><strong>年份:</strong> {{ script.periods or '默认' }}</div>
                    <div class="col-md-4"><strong>创建时间:</strong> {{ script.created_at }}</div>
                </div>
                {% if script.description %}
                <div class="row mt-2">
                    <div class="col-12"><strong>描述:</strong> {{ script.description }}</div>
                </div>
                {% endif %}
            </div>
            
            <div class="code-container">{{ script.code or '# 暂无代码' }}</div>
        </div>
    </body>
    </html>
    '''
    
    return render_template_string(code_template, script=script)


# 自定义报表视图 - 使用 Flask-Admin 布局
class ReportDashboardView(BaseView):
    """报表统计视图 - 嵌入 Flask-Admin 框架"""
    
    @expose('/')
    def index(self):
        if not session.get('admin_logged_in'):
            return redirect(url_for('login', next=request.url))
        return self.render_reports()
    
    def render_reports(self):
        """数据报表统计仪表盘 - 使用 Flask-Admin 布局"""
        from sqlalchemy import func
        
        # 获取统计数据
        stats = {
            'total_records': db_session.query(TradeData).count(),
            'confirmed_records': db_session.query(TradeData).filter_by(status='confirmed').count(),
            'pending_records': db_session.query(TradeData).filter_by(status='pending').count(),
            'total_value': db_session.query(func.sum(TradeData.export_value_usd)).scalar() or 0
        }
        
        # 按年份统计
        year_stats = db_session.query(
            TradeData.year,
            func.count(TradeData.id).label('count'),
            func.sum(TradeData.export_value_usd).label('total_value')
        ).group_by(TradeData.year).order_by(TradeData.year.desc()).all()
        
        # 按HS编码统计
        hs_stats = db_session.query(
            TradeData.hs_code,
            func.count(TradeData.id).label('count'),
            func.sum(TradeData.export_value_usd).label('total_value')
        ).group_by(TradeData.hs_code).order_by(func.sum(TradeData.export_value_usd).desc()).all()
        
        # 按贸易伙伴统计（Top 10）
        partner_stats = db_session.query(
            TradeData.trade_partner,
            func.count(TradeData.id).label('count'),
            func.sum(TradeData.export_value_usd).label('total_value')
        ).group_by(TradeData.trade_partner).order_by(func.sum(TradeData.export_value_usd).desc()).limit(10).all()
        
        # 数据来源统计
        source_stats = db_session.query(
            TradeData.data_source,
            func.count(TradeData.id).label('count')
        ).group_by(TradeData.data_source).all()
        
        # 使用内联模板
        return self.render('admin/report_dashboard.html',
            stats=stats,
            year_stats=year_stats,
            hs_stats=hs_stats,
            partner_stats=partner_stats,
            source_stats=source_stats
        )
    
    def is_accessible(self):
        return session.get('admin_logged_in') is True
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))


# 导出CSV
@app.route('/admin/export/trade-data')
@login_required
def export_trade_data():
    """导出外贸数据为CSV"""
    try:
        # 获取查询参数
        year = request.args.get('year', type=int)
        hs_code = request.args.get('hs_code')
        trade_partner = request.args.get('trade_partner')
        status = request.args.get('status', 'confirmed')
        
        # 构建查询
        query = db_session.query(TradeData)
        if year:
            query = query.filter(TradeData.year == year)
        if hs_code:
            query = query.filter(TradeData.hs_code.contains(hs_code))
        if trade_partner:
            query = query.filter(TradeData.trade_partner.contains(trade_partner))
        if status:
            query = query.filter(TradeData.status == status)
        
        data = query.all()
        
        # 生成CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        writer.writerow([
            'ID', '年份', 'HS编码', 'HS描述', '贸易伙伴', '出口数量', 
            '数量单位', '出口金额(USD)', '单价值(USD)', '贸易方式', 
            '数据来源', '状态', '创建时间'
        ])
        
        # 写入数据
        for item in data:
            writer.writerow([
                item.id,
                item.year,
                item.hs_code,
                item.hs_description or '',
                item.trade_partner,
                item.export_quantity or '',
                item.quantity_unit or '',
                item.export_value_usd or '',
                item.unit_value_usd or '',
                item.trade_mode or '',
                item.data_source or '',
                item.status,
                item.created_at.strftime('%Y-%m-%d %H:%M:%S') if item.created_at else ''
            ])
        
        # 记录审计日志
        audit_log = AuditLog(
            action='export_data',
            resource_type='trade_data',
            username=session.get('admin_username', 'admin'),
            ip_address=request.remote_addr,
            description=f'导出外贸数据: {len(data)}条记录'
        )
        db_session.add(audit_log)
        db_session.commit()
        
        # 返回CSV文件
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=trade_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            }
        )
    except Exception as e:
        flash(f'导出失败: {str(e)}', 'error')
        return redirect(url_for('admin_home'))


# 登录页面
@app.route('/login', methods=['GET', 'POST'])
def login():
    """管理员登录"""
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 验证用户
        user = db_session.query(User).filter_by(username=username).first()
        
        if user and user.role == 'admin' and password == 'admin123':
            session['admin_logged_in'] = True
            session['admin_username'] = username
            session['admin_user_id'] = user.id
            
            # 记录登录日志
            try:
                audit_log = AuditLog(
                    action='admin_login',
                    resource_type='system',
                    username=username,
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string if request.user_agent else '',
                    description='管理员登录系统'
                )
                db_session.add(audit_log)
                db_session.commit()
            except:
                db_session.rollback()
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin_home'))
        else:
            flash('用户名或密码错误，或您没有管理员权限', 'error')
    
    return render_template_string(LOGIN_TEMPLATE)


# 登出
@app.route('/logout')
def logout():
    """退出登录"""
    if session.get('admin_logged_in'):
        try:
            audit_log = AuditLog(
                action='admin_logout',
                resource_type='system',
                username=session.get('admin_username'),
                ip_address=request.remote_addr,
                description='管理员退出系统'
            )
            db_session.add(audit_log)
            db_session.commit()
        except:
            db_session.rollback()
    
    session.clear()
    return redirect(url_for('login'))


# 首页重定向
@app.route('/')
def index():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    return redirect(url_for('admin_home'))


# 健康检查
@app.route('/health')
def health():
    return {'status': 'healthy'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

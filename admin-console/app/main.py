"""
管理控制台 - Flask Admin
"""
import os
from flask import Flask, redirect, url_for
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from sqlalchemy.orm import scoped_session, sessionmaker

# 从 data-layer 导入
from data_layer import Base, engine
from data_layer.models import User, UserRole, CrawlerScript, CrawlerTask

# 创建应用
app = Flask(__name__)

# 配置
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'admin-secret-key')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'

# 数据库会话
Session = scoped_session(sessionmaker(bind=engine))
db_session = Session()


class UserAdmin(ModelView):
    column_list = ['id', 'username', 'email', 'full_name', 'role', 'is_active', 'created_at']
    column_searchable_list = ['username', 'email', 'full_name']
    column_filters = ['role', 'is_active', 'created_at']
    form_columns = ['username', 'email', 'full_name', 'role', 'is_active', 'is_superuser']
    can_create = True
    can_edit = True
    can_delete = True


class CrawlerScriptAdmin(ModelView):
    column_list = ['id', 'name', 'version', 'is_active', 'auto_run', 'created_at']
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


class CrawlerTaskAdmin(ModelView):
    column_list = ['id', 'script_name', 'status', 'started_at', 'completed_at', 'total_records', 'created_at']
    column_searchable_list = ['script_name']
    column_filters = ['status', 'trigger_type', 'created_at']
    can_create = False
    can_edit = False
    can_delete = False
    column_default_sort = ('created_at', True)


# 创建Admin
admin = Admin(
    app, 
    name='管理控制台', 
    template_mode='bootstrap4',
    base_template='admin/master.html'
)

# 添加视图
admin.add_view(UserAdmin(User, db_session, name='用户管理'))
admin.add_view(CrawlerScriptAdmin(CrawlerScript, db_session, name='爬虫脚本'))
admin.add_view(CrawlerTaskAdmin(CrawlerTask, db_session, name='爬虫任务'))


# 首页
@app.route('/')
def index():
    return redirect(url_for('admin.index'))


# 健康检查
@app.route('/health')
def health():
    return {'status': 'healthy'}


# CLI命令 - 创建管理员
@app.cli.command('create-admin')
def create_admin():
    """创建默认管理员用户"""
    from sqlalchemy import text
    
    result = db_session.execute(
        text("SELECT id FROM users WHERE username = 'admin'")
    ).fetchone()
    
    if result:
        print("管理员用户已存在")
        return
    
    db_session.execute(text("""
        INSERT INTO users (username, email, hashed_password, full_name, role, is_active, is_superuser, created_at)
        VALUES (
            'admin', 
            'admin@example.com',
            '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiAYMyzJ/I1m',
            '系统管理员',
            'admin',
            true,
            true,
            NOW()
        )
    """))
    db_session.commit()
    print("管理员用户创建成功")
    print("用户名: admin")
    print("密码: admin123")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

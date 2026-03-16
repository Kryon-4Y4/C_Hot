# 文档站点 - 使用单阶段构建避免镜像问题
FROM python:3.11-slim

WORKDIR /app

# 配置 pip 使用国内镜像源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# 安装MkDocs
RUN pip install mkdocs mkdocs-material

# 复制文档
COPY . .

# 构建文档
RUN mkdocs build

# 使用 Python 自带 http.server 提供静态文件
WORKDIR /app/site

EXPOSE 80

CMD ["python", "-m", "http.server", "80"]

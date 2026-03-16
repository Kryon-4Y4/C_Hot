FROM python:3.11-slim

WORKDIR /app

# 安装MkDocs
RUN pip install mkdocs mkdocs-material

# 复制文档
COPY . .

# 构建文档
RUN mkdocs build

# 使用nginx提供静态文件
FROM nginx:alpine

COPY --from=0 /app/site /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

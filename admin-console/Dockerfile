# Admin Console: 基于 data-layer 构建
FROM phone-parts/data-layer:latest

WORKDIR /app

# 复制 Admin Console 额外依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app/ ./app/

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["python", "-m", "app.main"]

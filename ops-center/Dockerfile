# Ops Center: 基于 data-layer 构建
FROM phone-parts/data-layer:latest

WORKDIR /app

# 复制运维中心额外依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app/ ./app/

# 暴露端口
EXPOSE 8001

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]

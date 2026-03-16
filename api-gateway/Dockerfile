# API Gateway: 基于 data-layer 构建
FROM phone-parts/data-layer:latest as builder

WORKDIR /app

# 复制 API Gateway 额外依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app/ ./app/

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# 用户门户 - 使用 Node 直接运行（避免 nginx 镜像问题）
FROM node:18-alpine

WORKDIR /app

# 配置 npm 使用国内镜像
RUN npm config set registry https://registry.npmmirror.com

# 复制依赖文件
COPY package.json .
RUN npm install

# 复制源码
COPY . .

# 构建
RUN npm run build

# 使用 serve 包提供静态文件
RUN npm install -g serve

EXPOSE 80

CMD ["serve", "-s", "dist", "-l", "80"]

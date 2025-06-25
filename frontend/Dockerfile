FROM node:18-alpine

WORKDIR /app

# 依存関係をコピーしてインストール
COPY package*.json ./
RUN npm ci --only=production

# アプリケーションコードをコピー
COPY . .

# Next.jsをビルド
RUN npm run build

# ポート3000を公開
EXPOSE 3000

# アプリケーション実行
CMD ["npm", "start"]
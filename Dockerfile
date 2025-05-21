# ----- Builder stage -----
FROM python:3.11-slim AS builder
WORKDIR /app

# 依存関係をインストール
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps -r requirements.txt -w /wheels

# ----- Final stage -----
FROM python:3.11-slim
WORKDIR /app

# ビルダーステージからホイールをコピー
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*

# アプリケーションコードをコピー
COPY . /app

# ポートを公開
EXPOSE 8501

# Streamlitアプリケーションを実行
CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"] 
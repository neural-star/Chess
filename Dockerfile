FROM python:3.11-slim

# 作業ディレクトリの設定
WORKDIR /app

# 必要ファイルをコピー
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリのコードをコピー
COPY app/ ./app

# 起動（Gradioなら）
CMD ["python", "app/main.py"]

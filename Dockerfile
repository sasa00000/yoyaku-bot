# Python 3.9の軽量版を使う
FROM python:3.9-slim

# 1. 必要なツールをインストール
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# 2. Chromeを直接ダウンロードしてインストール
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb

# 3. Pythonのライブラリをインストール
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. すべてのファイルをコピーしてアプリ起動
COPY . .
# ★ここを変更！ workers 1 で脳みそを一つにする
CMD ["gunicorn", "--bind", "0.0.0.0:80", "--workers", "1", "--threads", "8", "--timeout", "0", "app:app"]

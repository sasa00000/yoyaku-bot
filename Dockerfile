# Python 3.9が入ったベース環境を使う
FROM python:3.9-slim

# サーバーの基本ツールとChromeをインストール
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && apt-get clean

# 必要なPythonライブラリをインストール
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# すべてのファイルをサーバーにコピー
COPY . .

# アプリを起動（gunicornを使って安定させる）
CMD ["gunicorn", "--bind", "0.0.0.0:80", "app:app"]
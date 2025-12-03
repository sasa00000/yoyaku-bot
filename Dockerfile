# Python 3.9の軽量版を使う
FROM python:3.9-slim

# ★ここが追加ポイント1：環境変数を「アジア/東京」にする
ENV TZ=Asia/Tokyo
ENV PYTHONUNBUFFERED=1

# 1. 必要なツールをインストール
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    fonts-ipafont-gothic \
    fonts-noto-cjk \
    tzdata \
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

# 【重要2】Gunicornの設定を「お喋りモード」にする
# --access-logfile - : アクセスログを画面に出す
# --error-logfile -  : エラーログを画面に出す
# --capture-output   : Pythonのprint出力をキャッチして画面に出す
# --enable-stdio-inheritance : 標準出力を継承する
CMD ["gunicorn", "--bind", "0.0.0.0:80", "--workers", "1", "--threads", "8", "--timeout", "0", "--access-logfile", "-", "--error-logfile", "-", "--capture-output", "--enable-stdio-inheritance", "app:app"]

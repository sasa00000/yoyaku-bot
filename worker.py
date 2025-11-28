from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
from linebot import LineBotApi
from linebot.models import TextSendMessage
import os
import sys

# バッファリング（溜め込み）を強制的に無効化し、1行ごとに即出力させる
sys.stdout.reconfigure(line_buffering=True)

# ★状態管理用の変数（サーバーが生きている限り記憶される）
is_active = False     # 今動いているか？
should_stop = False   # 停止ボタンが押されたか？

# 環境変数から取得（なければ直書きのものを使用）
token = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', 'あなたのアクセストークンをここに貼る')
line_bot_api = LineBotApi(token)

# 通知先ID（自分）
MY_USER_ID = "U0e8b51c14790ae816195b924b2b6a1a4" 

# --- Selenium操作用関数（変更なし） ---
def text_field(driver, id, text):
    try:
        tf = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, id)))
        tf.clear()
        tf.send_keys(text)
    except:
        print(f"入力エラー: {id}")

def click(driver, selector):
    try:
        btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
        btn.click()
        sleep(1)
    except:
        print(f"クリックエラー: {selector}")

def check_cancellation(driver):
    # (既存のロジックそのまま)
    try:
        vacant_icons = driver.find_elements(By.XPATH, '//i[@title="空きあり" and text()="trip_origin"]')
        if len(vacant_icons) > 0:
            # ここでは簡易的に文字列を返します。本来は詳細取得ロジックを入れる
            return "どこかの区", "どこかの学校"
        return None, None
    except:
        return None, None

# ★この新しい関数を追加してください！
def smart_sleep(seconds):
    """停止命令を監視しながら待機する関数"""
    for _ in range(seconds):
        if should_stop: # もし停止命令が来てたら
            return      # すぐに待機をやめる
        sleep(1)

# --- ★停止命令を出す関数 ---
def stop_task():
    global should_stop
    should_stop = True
    print("停止命令が出されました")

# --- ★メイン実行関数 ---
def run_task(login_id, password, target_date):
    global is_active, should_stop
    
    # 二重起動防止
    if is_active:
        print("既に起動中です")
        return

    is_active = True
    should_stop = False
    
    print(f"Worker開始: {target_date} の予約を狙います")

    # ヘッドレスモード設定
    options = Options()
    options.add_argument('--headless') 
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    # run_task関数内のoptionsにこれを追加
    options.add_argument('--window-size=1280,1024')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36')
    
    driver = None

    try:
        driver = webdriver.Chrome(options=options)
        url = 'https://yoyaku.harp.lg.jp/sapporo/'
        driver.get(url)

        # ログイン
        click(driver, 'a.v-btn.v-btn--is-elevated.v-btn--has-bg.theme--light.v-size--default.white')
        text_field(driver, 'input-21', login_id) 
        text_field(driver, 'input-25', password)
        click(driver, 'button.v-btn.v-btn--is-elevated.v-btn--has-bg.success.is-main')
        print("ログイン成功")
        sleep(2)

        # 検索条件入力
        text_field(driver, 'input-15', 'その他(球技系)')
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@class="v-list-item__title" and text()="その他（球技系）"]'))
        ).click()
        
        text_field(driver, 'input-48', target_date)
        
        # 夜間チェックボックスなど
        try:
            night_checkbox = driver.find_element(By.ID, "input-80")
            driver.execute_script("arguments[0].click();", night_checkbox)
        except:
            pass

        sleep(1)
        # 検索ボタン2回クリック
        search_btn = 'button.SearchForm_simpleForm_searchBtn'
        click(driver, search_btn)
        click(driver, search_btn)

        while True:
            # ループの頭でチェック
            if should_stop:
                print("停止命令によりループを終了します")
                break

            driver.refresh()
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            district, school = check_cancellation(driver) 
            
            if school:
                # ... (通知処理) ...
                break 
            
            print("空きなし...再チェックします")
            
            # ★ここを sleep(10) ではなく smart_sleep(10) に変える！
            smart_sleep(10)
            
            # 待機中に停止ボタンが押された場合のために、ここでもチェック
            if should_stop:
                print("待機中に停止命令が来ました")
                break

    except Exception as e:
        print(f"エラー発生: {e}")
    finally:
        if driver:
            driver.quit()
        is_active = False # 停止状態に戻す
        print("Worker終了")

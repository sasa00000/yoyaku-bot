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

# ログ設定
sys.stdout.reconfigure(line_buffering=True)

# 変数
is_active = False
should_stop = False

# LINE設定
token = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', 'あなたのトークン')
line_bot_api = LineBotApi(token)
MY_USER_ID = "U0e8b51c14790ae816195b924b2b6a1a4" 

def smart_sleep(seconds):
    for _ in range(int(seconds)):
        if should_stop: return
        sleep(1)

def stop_task():
    global should_stop
    should_stop = True
    print("停止命令を受信しました")

def save_error_screenshot(driver, name):
    """エラー画面を撮影して保存する"""
    try:
        path = f"static/{name}.png"
        driver.save_screenshot(path)
        print(f"📸 エラー画面を保存しました: https://yoyaku-bot.onrender.com/{path}")
    except Exception as e:
        print(f"スクショ保存失敗: {e}")

# --- 操作関数 ---
def text_field(driver, id, text):
    if should_stop: return
    try:
        element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, id))
        )
        element.clear()
        element.send_keys(text)
    except Exception as e:
        print(f"入力エラー発生: {id}")
        save_error_screenshot(driver, "error_input") # ★ここで撮影
        raise e

def click(driver, selector):
    if should_stop: return
    try:
        element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
        )
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
        sleep(0.5)
        element.click()
    except Exception as e:
        print(f"クリックエラー発生: {selector}")
        save_error_screenshot(driver, "error_click") # ★ここで撮影
        raise e

def check_cancellation(driver):
    try:
        vacant_icons = driver.find_elements(By.XPATH, '//i[@title="空きあり" and text()="trip_origin"]')
        if len(vacant_icons) > 0:
            return "発見", "施設あり"
        return None, None
    except:
        return None, None

# --- メイン実行関数 ---
def run_task(login_id, password, target_date):
    global is_active, should_stop
    
    if is_active:
        print("既に起動中です")
        return

    is_active = True
    should_stop = False
    driver = None
    
    print(f"Worker開始: {target_date}")

    options = Options()
    # ★ステルス設定（ロボットバレを防ぐ）
    options.add_argument('--headless=new') 
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--lang=ja-JP') # 日本語環境にする
    # 「私はロボットです」という宣言を消す
    options.add_argument('--disable-blink-features=AutomationControlled') 
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36')

    try:
        driver = webdriver.Chrome(options=options)
        
        # サイトへアクセス
        url = 'https://yoyaku.harp.lg.jp/sapporo/'
        driver.get(url)
        print("サイトアクセス完了")

        # 念のためトップページも撮ってみる
        driver.save_screenshot('static/debug_top.png')

        # ログイン処理
        click(driver, 'a.v-btn.v-btn--is-elevated.v-btn--has-bg.theme--light.v-size--default.white')
        
        text_field(driver, 'input-21', login_id) 
        text_field(driver, 'input-25', password)
        
        click(driver, 'button.v-btn.v-btn--is-elevated.v-btn--has-bg.success.is-main')
        print("ログイン成功")
        sleep(3)

        # 検索条件入力
        text_field(driver, 'input-15', 'その他(球技系)')
        
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@class="v-list-item__title" and text()="その他（球技系）"]'))
        ).click()
        
        text_field(driver, 'input-48', target_date)
        
        try:
            driver.find_element(By.ID, "input-80").click()
        except:
            pass

        sleep(1)
        search_btn = 'button.SearchForm_simpleForm_searchBtn'
        click(driver, search_btn)
        click(driver, search_btn)
        
        # 監視ループ
        while not should_stop:
            driver.refresh()
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            district, school = check_cancellation(driver) 
            if school:
                line_bot_api.push_message(MY_USER_ID, TextSendMessage(text=f"{school}発見！"))
                break 
            
            print("空きなし...待機")
            smart_sleep(10)

    except Exception as e:
        print(f"エラー終了: {e}")
        # 念のため最後にも撮る
        if driver:
            driver.save_screenshot('static/error_final.png')
    finally:
        if driver:
            driver.quit()
        is_active = False 
        should_stop = False
        print("Worker停止")

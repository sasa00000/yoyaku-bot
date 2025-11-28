from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options # ヘッドレス用
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
from linebot import LineBotApi
from linebot.models import TextSendMessage

# ★セキュリティのため、トークンは環境変数管理が推奨ですが一旦そのまま記載
# (再発行した新しいトークンを使ってください)
YOUR_CHANNEL_ACCESS_TOKEN = '再発行したあなたのトークンをここに貼る'
line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)

# 通知先 (自分だけにするならこれ一つでOK)
MY_USER_ID = "U0e8b51c14790ae816195b924b2b6a1a4" 

# --- 以下、あなたの作った関数群 (基本そのまま) ---

def text_field(driver, id, text):
    """ドライバを引数で受け取るように変更"""
    tf = driver.find_element(By.ID, id)
    tf.send_keys(text)

def click(driver, id):
    button = driver.find_element(By.CSS_SELECTOR, id)
    button.click()
    sleep(1)

def safe_click(driver, xpath):
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, xpath))
    )
    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
    try:
        element.click()
    except:
        driver.execute_script("arguments[0].click();", element)

def check_cancellation(driver):
    # (あなたのcheck_cancellationコードの中身。長いので省略しますが、
    #  中の driver.find... を使うために driver を引数で渡す必要があります)
    # ※ロジックはそのままでOKですが、driver変数が使えるようにしてください
    try:
        vacant_icons = WebDriverWait(driver, 0.8).until(
            EC.presence_of_all_elements_located((By.XPATH, '//i[@title="空きあり" and text()="trip_origin"]'))
        )
        if len(vacant_icons) > 0:
            # ... (中略: あなたの発見ロジック) ...
            return "区名", "学校名" # 仮
        return None, None
    except:
        return None, None


# --- ★ここが改造のメイン！実行関数 ---

def run_task(login_id, password, target_date):
    """
    app.py から ID, Password, Date を受け取って実行する関数
    """
    print(f"Worker開始: {target_date} の予約を狙います")

    # Webアプリ化するなら「ヘッドレスモード」が必須
    options = Options()

    # ★サーバーでは画面が出せないので、必ずこの2行を有効にしてください！★
    options.add_argument('--headless') 
    options.add_argument('--no-sandbox') 
    options.add_argument('--disable-dev-shm-usage') # メモリ不足対策

    driver = webdriver.Chrome(options=options)

    url = 'https://yoyaku.harp.lg.jp/sapporo/'
    driver.get(url)

    # 定数
    FIRST_BUTTON = 'a.v-btn.v-btn--is-elevated.v-btn--has-bg.theme--light.v-size--default.white'
    LOGIN_BUTTON = 'button.v-btn.v-btn--is-elevated.v-btn--has-bg.success.is-main'
    SEARCH_BUTTON = 'button.SearchForm_simpleForm_searchBtn'

    try:
        # ログイン処理
        click(driver, FIRST_BUTTON)
        
        # ★ ここでHTMLから受け取った変数を使う！ ★
        text_field(driver, 'input-21', login_id) 
        text_field(driver, 'input-25', password)
        
        click(driver, LOGIN_BUTTON)
        print("ログイン成功")
        sleep(2)

        # 検索条件入力
        print("施設検索を開始します...")
        text_field(driver, 'input-15', 'その他(球技系)')
        
        list_item = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@class="v-list-item__title" and text()="その他（球技系）"]'))
        )
        list_item.click()
        
        # ★ ここでHTMLから受け取った変数を使う！ ★
        text_field(driver, 'input-48', target_date)
        
        night_checkbox = driver.find_element(By.ID, "input-80")
        driver.execute_script("arguments[0].click();", night_checkbox)
        
        sleep(3)
        click(driver, SEARCH_BUTTON)
        click(driver, SEARCH_BUTTON)

        # 無限ループ監視
        while True:
            driver.refresh()
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # check_cancellationなどは driver を渡して呼び出す
            district, school = check_cancellation(driver) 
            
            if school:
                # 予約処理 (あなたのコードの続き)
                line_bot_api.push_message(MY_USER_ID, TextSendMessage(text=f"{school}が取れました！"))
                break # 予約できたら終了
            
            sleep(5) # サーバー負荷軽減のため少し待つ

    except Exception as e:
        print(f"エラー発生: {e}")
    finally:
        driver.quit()
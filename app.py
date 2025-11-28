from flask import Flask, render_template, request, redirect, url_for
import threading
import time
import worker  # worker.py を読み込む

app = Flask(__name__)

@app.route('/')
def index():
    # workerが今動いているかを確認してHTMLに渡す
    return render_template('index.html', is_running=worker.is_active)

@app.route('/start', methods=['POST'])
def start():
    if worker.is_active:
        return redirect(url_for('index'))

    login_id = request.form['login_id']
    password = request.form['password']
    target_date = request.form['target_date']

    # スレッド起動
    thread = threading.Thread(
        target=worker.run_task,
        args=(login_id, password, target_date)
    )
    thread.start()

    return redirect(url_for('index'))

@app.route('/stop', methods=['POST'])
def stop():
    # 停止命令を出す
    worker.stop_task()
    
    # ★重要：裏で停止処理が完了するまで3秒くらい待ってあげる
    # そうしないと、画面がリロードされた時にまだ「稼働中」と判定されてしまう
    time.sleep(3)
    
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True, port=5000)

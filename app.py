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

# stop関数をこれに書き換え
@app.route('/stop', methods=['POST'])
def stop():
    worker.stop_task()
    
    # 完全に止まるまで最大20秒待つ（これが大事！）
    for _ in range(20):
        if not worker.is_active:
            break
        time.sleep(1)
    
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True, port=5000)

from flask import Flask, render_template, request
import threading
import worker  # worker.py を読み込む

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start():
    # HTMLフォームからデータを受け取る
    login_id = request.form['login_id']
    password = request.form['password']
    target_date = request.form['target_date']

    # 裏側（スレッド）でSeleniumを起動する
    # ここで worker.py の run_task 関数にデータを渡す！
    thread = threading.Thread(
        target=worker.run_task,
        args=(login_id, password, target_date)
    )
    thread.start()

    return f"""
    <h2>監視を開始しました！</h2>
    <ul>
        <li>ID: {login_id}</li>
        <li>日付: {target_date}</li>
    </ul>
    <p>このページは閉じても大丈夫です。</p>
    <a href="/">戻る</a>
    """

if __name__ == "__main__":
    app.run(debug=True, port=5000)
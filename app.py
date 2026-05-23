import sqlite3
import json
import random
import time
import os
from flask import Flask, request, redirect, url_for, render_template_string

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "games.db")


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS progress (
            user_id TEXT, game_name TEXT, state TEXT,
            score INTEGER DEFAULT 0, moves INTEGER DEFAULT 0,
            UNIQUE(user_id, game_name) ON CONFLICT REPLACE
        )""")
init_db()

def get_state(uid, game):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM progress WHERE user_id=? AND game_name=?", (uid, game)).fetchone()
        return json.loads(row["state"]) if row else None

def save_state(uid, game, state, score=0, moves=0):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT INTO progress (user_id, game_name, state, score, moves) VALUES (?,?,?,?,?)",
                     (uid, game, json.dumps(state), score, moves))



MENU_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>🎮 Игровой Портал</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 450px; margin: 40px auto; padding: 20px; background: #f8f9fa; color: #333; }
    h1 { text-align: center; margin-bottom: 30px; }
    .card { background: #fff; padding: 20px; margin: 15px 0; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); }
    .card h2 { margin: 0 0 10px; font-size: 1.3rem; }
    .card p { margin: 0 0 15px; color: #666; }
    .btn { display: block; width: 100%; padding: 12px; background: #4a90e2; color: #fff; text-align: center; text-decoration: none; border-radius: 8px; font-weight: 600; }
    .btn:hover { background: #357abd; }
    .uid { text-align: center; margin-top: 20px; font-size: 0.85rem; color: #888; }
  </style>
</head>
<body>
  <h1>🎮 Игровой Портал</h1>
  <div class="card">
    <h2>🔢 2048</h2>
    <p>Классическая головоломка. Соединяй числа до 2048.</p>
    <a class="btn" href="/2048?uid={{ uid }}">Играть</a>
  </div>
  <div class="card">
    <h2>🎰 Казино</h2>
    <p>Крути барабаны. Лови совпадения, копи монеты.</p>
    <a class="btn" href="/slots?uid={{ uid }}">Играть</a>
  </div>
  <div class="card">
    <h2>⌨️ Скорость ввода</h2>
    <p>Вводи слова на время. Бей свой рекорд.</p>
    <a class="btn" href="/typing?uid={{ uid }}">Играть</a>
  </div>
  <div class="uid">👤 ID: <strong>{{ uid }}</strong> • Меняй в URL для теста</div>
</body>
</html>
"""

GAME_2048_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title> 2048</title>
  <style>
    :root { --bg:#faf8ef; --text:#776e65; --grid:#bbada0; --empty:#cdc1b4; }
    body { margin:0; padding:16px; background:var(--bg); color:var(--text); font-family:system-ui,sans-serif; display:flex; justify-content:center; align-items:center; min-height:100vh; }
    .wrap { width:100%; max-width:340px; }
    header { display:flex; justify-content:space-between; margin-bottom:12px; font-weight:700; font-size:1.1rem; }
    .grid { display:grid; grid-template-columns:repeat(4,1fr); gap:8px; background:var(--grid); padding:8px; border-radius:8px; }
    .cell { aspect-ratio:1; display:flex; justify-content:center; align-items:center; background:var(--empty); border-radius:6px; font-weight:700; font-size:1.2rem; transition:background .2s; }
    .c2, .c4 { background:#eee4da; } .c8 { background:#f2b179; color:#fff; } .c16 { background:#f59563; color:#fff; }
    .c32 { background:#f67c5f; color:#fff; } .c64 { background:#f65e3b; color:#fff; }
    .c128, .c256, .c512 { background:#edcf72; color:#fff; font-size:1rem; } .c1024, .c2048 { background:#edcc61; color:#fff; font-size:.9rem; }
    .controls { display:flex; flex-direction:column; gap:8px; margin-top:16px; }
    .row { display:flex; gap:8px; justify-content:center; }
    button { flex:1; padding:14px; border:none; border-radius:6px; background:#8f7a66; color:#fff; font-weight:600; cursor:pointer; font-size:1rem; }
    button:disabled { opacity:0.4; cursor:not-allowed; }
    .status { text-align:center; margin:10px 0; font-weight:bold; } .win { color:#27ae60; } .lose { color:#e74c3c; }
    .back { display:block; margin-bottom:10px; color:#776e65; text-decoration:none; font-weight:600; }
  </style>
</head>
<body>
  <div class="wrap">
    <a class="back" href="/?uid={{ uid }}">← Меню</a>
    <header><span>Счёт: {{ score }}</span><span>Ходов: {{ moves }}</span></header>
    <div class="grid">
      {% for row in grid %}{% for cell in row %}<div class="cell {% if cell %}c{{ cell }}{% endif %}">{{ cell if cell else '' }}</div>{% endfor %}{% endfor %}
    </div>
    {% if over %}<div class="status {% if score >= 2048 %}win{% else %}lose{% endif %}">{% if score >= 2048 %}🎉 Ты собрал 2048!{% else %}🏁 Ходы закончились{% endif %}</div>{% endif %}
    <form class="controls" method="POST" action="/2048/move">
      <input type="hidden" name="uid" value="{{ uid }}">
      <div class="row"><button name="dir" value="up" {% if over %}disabled{% endif %}>⬆️</button></div>
      <div class="row"><button name="dir" value="left" {% if over %}disabled{% endif %}>⬅️</button><button name="dir" value="right" {% if over %}disabled{% endif %}>➡️</button></div>
      <div class="row"><button name="dir" value="down" {% if over %}disabled{% endif %}>⬇️</button></div>
    </form>
    <form method="POST" action="/2048/reset" style="margin-top:12px;"><input type="hidden" name="uid" value="{{ uid }}"><button style="background:#555; width:100%;" type="submit">🔄 Начать заново</button></form>
  </div>
</body>
</html>
"""

GAME_SLOTS_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>🎰 Казино</title>
  <style>
    body { font-family: system-ui; text-align: center; padding: 20px; background: #1a1a2e; color: #eaeaea; }
    .reels { display: flex; justify-content: center; gap: 10px; margin: 20px 0; font-size: 3rem; }
    .reel { background: #16213e; padding: 15px 20px; border-radius: 10px; border: 2px solid #0f3460; }
    .balance { font-size: 1.2rem; margin-bottom: 10px; }
    .msg { min-height: 1.5rem; margin: 10px 0; font-weight: 500; color: #ffd166; }
    .spin-btn { background: #e63946; color: #fff; border: none; padding: 15px 30px; font-size: 1.2rem; border-radius: 8px; cursor: pointer; }
    .spin-btn:disabled { background: #555; cursor: not-allowed; }
    .reset { background: #4a4e69; color: #fff; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; margin-top: 10px; }
    .back { display: block; margin-top: 20px; color: #a8dadc; text-decoration: none; }
  </style>
</head>
<body>
  <a class="back" href="/?uid={{ uid }}">← Меню</a>
  <h1>🎰 Казино</h1>
  <div class="balance"> Баланс: {{ balance }} | 🎰 Спинов: {{ spins }} | 🏆 Побед: {{ wins }}</div>
  <div class="reels"><div class="reel">{{ reels[0] }}</div><div class="reel">{{ reels[1] }}</div><div class="reel">{{ reels[2] }}</div></div>
  <div class="msg">{{ msg }}</div>
  <form method="POST" action="/slots/spin">
    <input type="hidden" name="uid" value="{{ uid }}">
    <button class="spin-btn" type="submit" {% if balance < 10 %}disabled{% endif %}>🎲 SPIN (10 монет)</button>
  </form>
  <form method="POST" action="/slots/reset">
    <input type="hidden" name="uid" value="{{ uid }}">
    <button class="reset" type="submit">🔄 Сбросить прогресс</button>
  </form>
</body>
</html>
"""

GAME_TYPING_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>⌨️ Скорость ввода</title>
  <style>
    body { font-family: system-ui; text-align: center; padding: 20px; background: #f0f4f8; color: #2d3748; }
    .target { font-size: 2.5rem; font-weight: bold; margin: 20px 0; color: #2b6cb0; background: #ebf8ff; padding: 15px; border-radius: 10px; }
    input[type="text"] { width: 80%; max-width: 300px; padding: 12px; font-size: 1.2rem; border: 2px solid #cbd5e0; border-radius: 8px; text-align: center; }
    .submit-btn { background: #48bb78; color: #fff; border: none; padding: 12px 24px; font-size: 1rem; border-radius: 8px; cursor: pointer; margin-top: 10px; }
    .stats { display: flex; justify-content: space-around; margin: 20px 0; font-size: 0.95rem; }
    .stat-box { background: #fff; padding: 10px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .result { margin: 10px 0; font-weight: 600; min-height: 1.5rem; }
    .back { display: block; margin-top: 20px; color: #718096; text-decoration: none; }
  </style>
</head>
<body>
  <a class="back" href="/?uid={{ uid }}">← Меню</a>
  <h1>⌨️ Скорость ввода</h1>
  <div class="stats">
    <div class="stat-box"> Лучшее: {{ "%.2f"|format(best_time) }} сек</div>
    <div class="stat-box">✅ Верно: {{ correct }}/{{ total }}</div>
  </div>
  <div class="target">{{ word }}</div>
  <div class="result" style="color: {{ 'green' if 'Верно' in result else ('red' if 'Ошибка' in result else 'gray') }}">{{ result }}</div>
  <div style="color: #718096; margin-bottom: 10px;">⏱️ Последнее: {{ last_time }}</div>
  <form method="POST" action="/typing/check">
    <input type="hidden" name="uid" value="{{ uid }}">
    <input type="text" name="input" placeholder="Введи слово..." autocomplete="off" autofocus>
    <br><button class="submit-btn" type="submit">Проверить</button>
  </form>
  <form method="POST" action="/typing/reset">
    <input type="hidden" name="uid" value="{{ uid }}">
    <button class="submit-btn" style="background: #a0aec0; margin-top: 10px;" type="submit">🔄 Сбросить</button>
  </form>
</body>
</html>
"""




def init_2048():
    grid = [[0]*4 for _ in range(4)]
    spawn_2048(grid); spawn_2048(grid)
    return {"grid": grid, "score": 0, "moves": 0}

def spawn_2048(grid):
    empty = [(r,c) for r in range(4) for c in range(4) if grid[r][c]==0]
    if empty: r,c = random.choice(empty); grid[r][c] = 4 if random.random()<0.1 else 2

def merge_2048(line):
    arr = [x for x in line if x!=0]; res, pts = [], 0; i=0
    while i<len(arr):
        if i+1<len(arr) and arr[i]==arr[i+1]: val=arr[i]*2; res.append(val); pts+=val; i+=2
        else: res.append(arr[i]); i+=1
    return res+[0]*(4-len(res)), pts

def move_2048(grid, direction):
    moved, added = False, 0
    if direction in ("left","right"):
        for r in range(4):
            row = grid[r][::-1] if direction=="right" else grid[r]
            new, pts = merge_2048(row)
            if direction=="right": new=new[::-1]
            if grid[r]!=new: moved=True
            grid[r]=new; added+=pts
    else:
        for c in range(4):
            col=[grid[r][c] for r in range(4)]
            if direction=="down": col=col[::-1]
            new, pts = merge_2048(col)
            if direction=="down": new=new[::-1]
            if col!=new: moved=True
            for r in range(4): grid[r][c]=new[r]; added+=pts
    return moved, added

def is_2048_over(grid):
    if any(0 in row for row in grid): return False
    for r in range(4):
        for c in range(3):
            if grid[r][c]==grid[r][c+1]: return False
    for c in range(4):
        for r in range(3):
            if grid[r][c]==grid[r+1][c]: return False
    return True


SYMBOLS = ['🍒', '🍋', '🍇', '🍉', '💎', '7️']
BET = 10
def init_slots():
    return {"balance": 100, "reels": ["❓","❓","❓"], "msg": "Нажми SPIN! Ставка: 10 монет", "spins": 0, "wins": 0}
def spin_slots(state):
    if state["balance"] < BET: state["msg"] = "💸 Недостаточно монет!"; return state
    state["balance"] -= BET; state["spins"] += 1
    reels = [random.choice(SYMBOLS) for _ in range(3)]; state["reels"] = reels
    if reels[0] == reels[1] == reels[2]:
        win = BET * 10; state["balance"] += win; state["wins"] += 1; state["msg"] = f" ДЖЕКПОТ! +{win} монет!"
    elif reels[0]==reels[1] or reels[1]==reels[2] or reels[0]==reels[2]:
        win = BET * 2; state["balance"] += win; state["wins"] += 1; state["msg"] = f"✨ Два совпадения! +{win} монет"
    else: state["msg"] = "😢 Не повезло."
    return state


WORDS = ["питон", "фласк", "сервер", "база", "данные", "алгоритм", "функция", "класс", "модуль", "переменная", "цикл", "условие", "строка", "список", "индекс", "проект", "тест", "код", "скрипт", "массив"]
def init_typing():
    return {"word": random.choice(WORDS), "start": time.time(), "best_time": 999.0, "correct": 0, "total": 0, "result": "Введи слово и нажми ENTER", "last_time": "-"}
def check_typing(state, user_input):
    state["total"] += 1; elapsed = time.time() - state["start"]
    if user_input.strip().lower() == state["word"]:
        state["correct"] += 1; state["result"] = "✅ Верно! Отличная скорость!"
        state["last_time"] = f"{elapsed:.2f} сек"
        if elapsed < state["best_time"]: state["best_time"] = elapsed
        state["word"] = random.choice(WORDS); state["start"] = time.time()
    else:
        state["result"] = f"❌ Ошибка! Было: {state['word']}"; state["last_time"] = f"{elapsed:.2f} сек"; state["start"] = time.time()
    return state



@app.route("/")
def menu():
    return render_template_string(MENU_HTML, uid=request.args.get('uid', 'player'))

@app.route("/2048")
def game_2048():
    uid = request.args.get("uid", "player")
    state = get_state(uid, "2048") or init_2048()
    state["over"] = is_2048_over(state["grid"])
    return render_template_string(GAME_2048_HTML, **state, uid=uid)

@app.route("/2048/move", methods=["POST"])
def handle_2048():
    uid, direction = request.form["uid"], request.form["dir"]
    state = get_state(uid, "2048") or init_2048()
    if not is_2048_over(state["grid"]):
        moved, pts = move_2048(state["grid"], direction)
        if moved: state["score"] += pts; state["moves"] += 1; spawn_2048(state["grid"])
    save_state(uid, "2048", state, state["score"], state["moves"])
    return redirect(url_for("game_2048", uid=uid))

@app.route("/2048/reset", methods=["POST"])
def reset_2048():
    uid = request.form["uid"]
    save_state(uid, "2048", init_2048(), 0, 0)
    return redirect(url_for("game_2048", uid=uid))

@app.route("/slots")
def game_slots():
    uid = request.args.get("uid", "player")
    state = get_state(uid, "slots") or init_slots()
    return render_template_string(GAME_SLOTS_HTML, **state, uid=uid)

@app.route("/slots/spin", methods=["POST"])
def handle_slots():
    uid = request.form["uid"]
    state = get_state(uid, "slots") or init_slots()
    state = spin_slots(state)
    save_state(uid, "slots", state, state["balance"], state["spins"])
    return redirect(url_for("game_slots", uid=uid))

@app.route("/slots/reset", methods=["POST"])
def reset_slots():
    uid = request.form["uid"]
    save_state(uid, "slots", init_slots(), 100, 0)
    return redirect(url_for("game_slots", uid=uid))

@app.route("/typing")
def game_typing():
    uid = request.args.get("uid", "player")
    state = get_state(uid, "typing") or init_typing()
    return render_template_string(GAME_TYPING_HTML, **state, uid=uid)

@app.route("/typing/check", methods=["POST"])
def handle_typing():
    uid = request.form["uid"]
    user_input = request.form["input"]
    state = get_state(uid, "typing") or init_typing()
    state = check_typing(state, user_input)
    save_state(uid, "typing", state, int(state["correct"]), state["total"])
    return redirect(url_for("game_typing", uid=uid))

@app.route("/typing/reset", methods=["POST"])
def reset_typing():
    uid = request.form["uid"]
    save_state(uid, "typing", init_typing(), 0, 0)
    return redirect(url_for("game_typing", uid=uid))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
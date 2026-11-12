import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for

# Автоматическое создание структуры папок для Flask
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
if not os.path.exists(TEMPLATE_DIR):
    os.makedirs(TEMPLATE_DIR)

# HTML-интерфейс 1-й версии программы
HTML_CONTENT_V1 = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Расчет мероприятий</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #f8f9fa; margin: 0; padding: 25px; }
        .container { display: flex; max-width: 1200px; margin: 0 auto; gap: 25px; }
        .form-panel, .archive-panel { background: white; border: 1px solid #dee2e6; padding: 25px; border-radius: 8px; }
        .form-panel { flex: 1; } .archive-panel { flex: 1.5; }
        h2 { margin-top: 0; border-bottom: 2px solid #e9ecef; padding-bottom: 10px; color: #495057; }
        label { display: block; margin: 12px 0 4px; font-weight: 600; }
        input, select { width: 100%; padding: 10px; box-sizing: border-box; border: 1px solid #ced4da; border-radius: 4px; }
        button { width: 100%; padding: 12px; background-color: #ffa500; color: black; border: none; border-radius: 4px; font-size: 16px; font-weight: bold; cursor: pointer; margin-top: 25px; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { border: 1px solid #dee2e6; padding: 12px; text-align: left; }
        th { background-color: #f1f3f5; }
    </style>
</head>
<body>
<div class="container">
    <div class="form-panel">
        <h2>Расчет стоимости</h2>
        <form action="/add_event" method="POST">
            <label>Название мероприятия:</label>
            <input type="text" name="client_name" placeholder="Иванов И.И. / Свадьба" required>
            <label>Выберите тариф обслуживания:</label>
            <select name="package">
                <option value="Бюджетный">Бюджетный(15 000)</option>
                <option value="Стандарт" selected>Стандарт(35 000)</option>
                <option value="VIP">VIP(75 000)</option>
            </select>
            <button type="submit">Рассчитать стоимость</button>
        </form>
    </div>
    <div class="archive-panel">
        <h2>История расчетов</h2>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Мероприятие / Заказчик</th>
                    <th>Тариф</th>
                    <th>Итоговая стоимость</th>
                </tr>
            </thead>
            <tbody>
                {% for event in events %}
                <tr>
                    <td>{{ event[0] }}</td>
                    <td><b>{{ event[1] }}</b></td>
                    <td>{{ event[2] }}</td>
                    <td style="color: darkgreen; font-weight: bold;">{{ "{:,.1f}".format(event[3]) }} руб.</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
</body>
</html>
"""

with open(os.path.join(TEMPLATE_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(HTML_CONTENT_V1)

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "events_agency_v1.db")

def init_db_v1():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Удаляем старую структуру для корректного наката v1
    cursor.execute("DROP TABLE IF EXISTS events_orders")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT,
            tariff TEXT,
            total_cost REAL
        )
    """)

    # Автоматическое добавление тестовых строчек для вычислительного эксперимента
    cursor.execute("SELECT COUNT(*) FROM events_orders")
    if cursor.fetchone()[0] == 0:
        test_data = [
            ("Петров А.В. / День рождения", "Бюджетный", 15000.0),
            ("Сидоров К.М. / Корпоратив", "Стандарт", 35000.0),
            ("Халтурина Е.С. / Юбилей", "VIP", 75000.0)
        ]
        cursor.executemany("INSERT INTO events_orders (client_name, tariff, total_cost) VALUES (?, ?, ?)", test_data)
    conn.commit()
    conn.close()


@app.route("/")
def index():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, client_name, tariff, total_cost FROM events_orders ORDER BY id DESC")
    events = cursor.fetchall()
    conn.close()
    return render_template("index.html", events=events)


@app.route("/add_event", methods=["POST"])
def add_event():
    client = request.form.get("client_name")
    package = request.form.get("package")

    if client:
        tariff_prices = {"Бюджетный": 15000.0, "Стандарт": 35000.0, "VIP": 75000.0}
        cost = tariff_prices.get(package, 0.0)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO events_orders (client_name, tariff, total_cost) VALUES (?, ?, ?)",
                       (client, package, cost))
        conn.commit()
        conn.close()
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db_v1()
    app.run(debug=True, port=5000)
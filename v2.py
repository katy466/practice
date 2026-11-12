import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for

# Автоматическое создание структуры папок для шаблонов Flask
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
if not os.path.exists(TEMPLATE_DIR):
    os.makedirs(TEMPLATE_DIR)

# HTML-интерфейс 2-й версии программы (Расширенный веб-стиль оформления)
HTML_CONTENT_V2 = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Агентство праздников</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #f8f9fa; margin: 0; padding: 25px; color: #212529; }
        .container { display: flex; max-width: 1300px; margin: 0 auto; gap: 25px; }
        .form-panel, .archive-panel { background: white; border: 1px solid #dee2e6; padding: 25px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.03); }
        .form-panel { flex: 1; } .archive-panel { flex: 1.8; }
        h2 { margin-top: 0; font-size: 22px; color: #495057; border-bottom: 2px solid #e9ecef; padding-bottom: 10px; }
        h2.gray { color: #6c757d; }
        label { display: block; margin: 12px 0 4px; font-size: 14px; font-weight: 600; }
        input, select { width: 100%; padding: 10px; box-sizing: border-box; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px; }
        button { width: 100%; padding: 12px; background-color: #007bff; color: white; border: none; border-radius: 4px; font-size: 16px; font-weight: bold; cursor: pointer; margin-top: 25px; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { border: 1px solid #dee2e6; padding: 12px; text-align: left; font-size: 13px; }
        th { background-color: #f1f3f5; font-weight: 600; }
        .status-badge { background-color: #28a745; color: white; padding: 3px 8px; border-radius: 20px; font-size: 11px; font-weight: bold; text-transform: uppercase; }
    </style>
</head>
<body>
<div class="container">
    <!-- Левая колонка: Интерактивная форма ввода данных -->
    <div class="form-panel">
        <h2>Оформление мероприятия</h2>
        <form action="/add_event" method="POST">
            <label>ФИО:</label>
            <input type="text" name="client_name" placeholder="Иванов Иван Иванович" required>
            <label>Тип мероприятия:</label>
            <select name="event_type">
                <option value="Свадьба">Свадьба</option>
                <option value="Корпоратив">Корпоратив</option>
                <option value="День рождения">День рождения</option>
                <option value="Выпускной">Выпускной</option>
            </select>
            <label>Количество гостей:</label>
            <input type="number" name="guests_count" min="1" value="20" required>
            <label>Пакет услуг агентства:</label>
            <select name="package">
                <option value="Бюджетный">Бюджетный (Только аренда)</option>
                <option value="Стандарт" selected>Стандарт (Зал + Декор)</option>
                <option value="Premium">Premium (Все включено)</option>
            </select>
            <label>Назначить ответственного ведущего:</label>
            <select name="organizer_id">
                {% for org in organizers %}
                    <option value="{{ org[0] }}">{{ org[1] }}</option>
                {% endfor %}
            </select>
            <button type="submit">Рассчитать смету и сохранить</button>
        </form>
    </div>
    <!-- Правая колонка: Логирование вычислительного эксперимента (БД SQLite) -->
    <div class="archive-panel">
        <h2 class="gray">АРХИВ ОФОРМЛЕННЫХ МЕРОПРИЯТИЙ</h2>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Заказчик</th>
                    <th>Тип события</th>
                    <th>Гости</th>
                    <th>Организатор</th>
                    <th>Итоговая смета</th>
                    <th>Статус</th>
                </tr>
            </thead>
            <tbody>
                {% for event in events %}
                <tr>
                    <td>{{ event[0] }}</td>
                    <td><b>{{ event[1] }}</b></td>
                    <td>{{ event[2] }}</td>
                    <td>{{ event[3] }} чел.</td>
                    <td>{{ event[4] }}</td>
                    <td style="color: #28a745; font-weight: bold;">{{ "{:,.2f}".format(event[5]) }} ₽</td>
                    <td><span class="status-badge">{{ event[6] }}</span></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
</body>
</html>
"""

# Автоматическая генерация HTML-файла в папке templates
with open(os.path.join(TEMPLATE_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(HTML_CONTENT_V2)

app = Flask(__name__)

# Использование уникального имени файла базы данных v2 для обхода блокировок
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "events_agency_v2.db")


# Инициализация структуры таблиц СУБД SQLite
def init_db_v2():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Создание таблицы персонала/организаторов
    cursor.execute("CREATE TABLE IF NOT EXISTS organizers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)")

    # 2. Создание основной таблицы заказов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT,
            event_type TEXT,
            guests_count INTEGER,
            organizer_id INTEGER,
            total_cost REAL,
            status TEXT,
            FOREIGN KEY(organizer_id) REFERENCES organizers(id)
        )
    """)

    # Автозаполнение справочника ведущих, если он пуст
    cursor.execute("SELECT COUNT(*) FROM organizers")
    if cursor.fetchone()[0] == 0:
        team = [
            ("Александр Рева (Ведущий VIP)",),
            ("Елена Блиновская (Координатор)",),
            ("Шоу-балет 'Кристалл' (Анимация)",)
        ]
        cursor.executemany("INSERT INTO organizers (name) VALUES (?)", team)

    # Автозаполнение тестовых строчек для вычислительного эксперимента
    cursor.execute("SELECT COUNT(*) FROM events_orders")
    if cursor.fetchone()[0] == 0:
        test_events = [
            ("Смирнов А.П.", "Свадьба", 50, 1, 300000.0, "ПОДТВЕРЖДЕНО"),
            ("Васильева О.Н.", "День рождения", 15, 2, 105000.0, "ПОДТВЕРЖДЕНО"),
            ("Халтурина К.C.", "Корпоратив", 100, 3, 450000.0, "ПОДТВЕРЖДЕНО")
        ]
        cursor.executemany("""
            INSERT INTO events_orders (client_name, event_type, guests_count, organizer_id, total_cost, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, test_events)

    conn.commit()
    conn.close()


@app.route("/")
def index():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM organizers")
    organizers = cursor.fetchall()

    # Сквозная выборка из базы с помощью JOIN
    cursor.execute("""
        SELECT e.id, e.client_name, e.event_type, e.guests_count, o.name, e.total_cost, e.status 
        FROM events_orders e
        JOIN organizers o ON e.organizer_id = o.id
        ORDER BY e.id DESC
    """)
    events = cursor.fetchall()
    conn.close()
    return render_template("index.html", organizers=organizers, events=events)


@app.route("/add_event", methods=["POST"])
def add_event():
    client = request.form.get("client_name")
    event_type = request.form.get("event_type")
    guests = int(request.form.get("guests_count", 0))
    organizer_id = int(request.form.get("organizer_id"))
    package = request.form.get("package")

    if client:
        # Бизнес-логика калькуляции сметы: Фиксированный пакет + (Количество гостей * 3000 рублей банкетное меню)
        package_rates = {"Бюджетный": 25000.0, "Стандарт": 60000.0, "Premium": 150000.0}
        base_cost = package_rates.get(package, 30000.0)
        catering_cost = guests * 3000.0
        total_cost = base_cost + catering_cost

        # Запись новой строки логов напрямую в СУБД SQLite
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO events_orders (client_name, event_type, guests_count, organizer_id, total_cost, status)
            VALUES (?, ?, ?, ?, ?, 'ПОДТВЕРЖДЕНО')
        """, (client, event_type, guests, organizer_id, total_cost))
        conn.commit()
        conn.close()
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db_v2()
    app.run(debug=True, port=5000)

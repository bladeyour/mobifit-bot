from flask import Flask, request
import os
import requests

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")
API_URL = f"https://api.telegram.org/bot{TOKEN}"

user_data = {}

def send_message(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(f"{API_URL}/sendMessage", json=payload)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if "message" not in data:
        return "", 200

    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "").strip()

    if chat_id not in user_data:
        user_data[chat_id] = {}

    state = user_data[chat_id]

    if text == "/start":
        user_data[chat_id] = {}
        reply_markup = {
            "keyboard": [[{"text": "👨 Чоловіча"}], [{"text": "👩 Жіноча"}]],
            "one_time_keyboard": True,
            "resize_keyboard": True
        }
        send_message(chat_id, "Привіт! Я Mobifit — твій ШІ-фітнес-тренер 💪\n\nОберіть свою стать:", reply_markup)
        return "", 200

    if "gender" not in state:
        if "чоловіча" in text.lower():
            state["gender"] = "male"
        elif "жіноча" in text.lower():
            state["gender"] = "female"
        else:
            send_message(chat_id, "Будь ласка, оберіть стать: 👨 або 👩")
            return "", 200
        send_message(chat_id, "Скільки вам років?")
        return "", 200

    if "age" not in state:
        if text.isdigit():
            state["age"] = int(text)
            send_message(chat_id, "Введіть ваш зріст у см:")
        else:
            send_message(chat_id, "Введіть коректний вік (число):")
        return "", 200

    if "height" not in state:
        if text.isdigit():
            state["height"] = int(text)
            send_message(chat_id, "Введіть вашу вагу в кг:")
        else:
            send_message(chat_id, "Введіть зріст числом у см:")
        return "", 200

    if "weight" not in state:
        if text.isdigit():
            state["weight"] = int(text)
            reply_markup = {
                "keyboard": [[{"text": "⚖️ Схуднути"}], [{"text": "💪 Набрати"}], [{"text": "🧘 Підтримувати"}]],
                "one_time_keyboard": True,
                "resize_keyboard": True
            }
            send_message(chat_id, "Яка ваша мета?", reply_markup)
        else:
            send_message(chat_id, "Введіть вагу числом у кг:")
        return "", 200

    if "goal" not in state:
        goals = {"схуднути": "cut", "набрати": "bulk", "підтримувати": "maintain"}
        for key in goals:
            if key in text.lower():
                state["goal"] = goals[key]
                return generate_plan(chat_id, state)
        send_message(chat_id, "Оберіть мету: ⚖️ / 💪 / 🧘")
        return "", 200

    return "", 200

def generate_plan(chat_id, state):
    age = state["age"]
    height = state["height"]
    weight = state["weight"]
    gender = state["gender"]
    goal = state["goal"]

    # BMR (Mifflin–St Jeor)
    if gender == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    # Activity multiplier (легка активність)
    calories = int(bmr * 1.4)

    if goal == "cut":
        calories -= 300
    elif goal == "bulk":
        calories += 300

    protein = int(weight * 1.8)
    water = round(weight * 0.035, 2)

    goal_text = {
        "cut": "⚖️ Схуднення",
        "bulk": "💪 Набір маси",
        "maintain": "🧘 Підтримка форми"
    }

    plan = f"""
*📊 Ваш персональний фітнес-план:*

*Стать:* {'Чоловіча' if gender == 'male' else 'Жіноча'}
*Вік:* {age}
*Зріст:* {height} см
*Вага:* {weight} кг
*Мета:* {goal_text[goal]}

*🔥 Калорій на день:* {calories} ккал
*🥩 Білків:* {protein} г/день
*💧 Води:* {water} л/день

*🏋️ Тренування (рекомендація):*
- Пн: Силові (ноги + прес)
- Вт: Кардіо 30–40 хв
- Ср: Верх тіла + спина
- Чт: Відпочинок
- Пт: Силові (груди + плечі)
- Сб: Йога або активна прогулянка
- Нд: Відпочинок або легке кардіо

Почнемо? 💪
"""

    send_message(chat_id, plan)
    return "", 200

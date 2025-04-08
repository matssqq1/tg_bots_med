import requests
import time
from transformers import pipeline
from googletrans import Translator
import asyncio

# Загрузка предобученной модели для анализа эмоций
emotion_analysis = pipeline("text-classification", model="SamLowe/roberta-base-go_emotions")

# Словарь для перевода эмоций на русский язык
emotion_translation = {
    "admiration": "восхищение",
    "amusement": "развлечение",
    "anger": "гнев",
    "annoyance": "раздражение",
    "approval": "одобрение",
    "caring": "забота",
    "confusion": "замешательство",
    "curiosity": "любопытство",
    "desire": "желание",
    "disappointment": "разочарование",
    "disapproval": "неодобрение",
    "disgust": "отвращение",
    "embarrassment": "смущение",
    "excitement": "возбуждение",
    "fear": "страх",
    "gratitude": "благодарность",
    "grief": "горе",
    "joy": "радость",
    "love": "любовь",
    "nervousness": "нервозность",
    "optimism": "оптимизм",
    "pride": "гордость",
    "realization": "осознание",
    "relief": "облегчение",
    "remorse": "раскаяние",
    "sadness": "печаль",
    "surprise": "удивление",
    "neutral": "нейтрально"
}

# Инициализация переводчика
translator = Translator()

# Вставьте свой токен API здесь
TOKEN = "7903635056:AAHXpZ-VHzJY2C63q_UvrnIIDIpShfpG5FY"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# Функция для получения новых сообщений
def get_updates(offset=None):
    url = f"{BASE_URL}/getUpdates"
    params = {"timeout": 100, "offset": offset}
    response = requests.get(url, params=params)
    return response.json()

# Функция для отправки сообщений
def send_message(chat_id, text):
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    response = requests.post(url, json=payload)
    return response.json()

# Функция для анализа давления в зависимости от возраста
def analyze_pressure_by_age(age, systolic, diastolic):
    if age < 18:
        normal_range = (90, 120, 60, 80)  # примерные диапазоны для подростков
    elif 18 <= age < 30:
        normal_range = (90, 120, 60, 80)
    elif 30 <= age < 40:
        normal_range = (90, 120, 60, 80)
    elif 40 <= age < 50:
        normal_range = (90, 130, 60, 85)
    elif 50 <= age < 60:
        normal_range = (90, 140, 60, 90)
    elif 60 <= age < 70:
        normal_range = (110, 150, 70, 95)
    else:
        normal_range = (110, 160, 70, 100)
    
    systolic_min, systolic_max, diastolic_min, diastolic_max = normal_range
    
    if systolic > systolic_max or diastolic > diastolic_max:
        return f"Высокое давление для вашего возраста ({age}). Рекомендуется обратиться к врачу."
    elif systolic < systolic_min or diastolic < diastolic_min:
        return f"Низкое давление для вашего возраста ({age}). Рекомендуется обратиться к врачу."
    else:
        return f"Давление в норме для вашего возраста ({age})."

# Основной цикл бота
async def main():
    last_update_id = None
    print("Бот запущен...")
    
    while True:
        try:
            # Получаем новые сообщения
            updates = get_updates(last_update_id)
            
            if updates["result"]:
                for update in updates["result"]:
                    # Проверяем наличие ключа "message" в объекте update
                    if "message" not in update:
                        continue
                    
                    # Извлекаем данные из сообщения
                    update_id = update["update_id"]
                    chat_id = update["message"]["chat"]["id"]
                    user_text = update["message"].get("text", "")
                    
                    # Обновляем ID последнего сообщения
                    last_update_id = update_id + 1
                    
                    # Проверяем команду /start
                    if user_text == "/start":
                        welcome_message = (
                            "👋 Привет! Я бот для анализа ментального здоровья и дваления. "
                            "Отправьте мне текст (например, свои мысли или чувства), "
                            "и я помогу проанализировать его эмоциональную окраску.\n"
                            "Для анализа давления используйте команду /dawlenie <возраст> <систолическое> <диастолическое>"
                        )
                        send_message(chat_id, welcome_message)
                        continue
                    
                    # Проверяем команду /dawlenie
                    if user_text.startswith("/dawlenie"):
                        parts = user_text.split()
                        if len(parts) != 4:
                            send_message(chat_id, "Используйте команду /dawlenие <возраст> <систолическое> <диастолическое>")
                            continue
                        
                        try:
                            age = int(parts[1])
                            systolic = int(parts[2])
                            diastolic = int(parts[3])
                            result = analyze_pressure_by_age(age, systolic, diastolic)
                            send_message(chat_id, result)
                        except ValueError:
                            send_message(chat_id, "Введите корректные числовые значения.")
                        continue
                    
                    # Проверяем, что текст не пустой
                    if not user_text.strip():
                        send_message(chat_id, "Пожалуйста, отправьте текст для анализа.")
                        continue
                    
                    # Переводим текст на английский
                    try:
                        translated_text = await translator.translate(user_text, src="ru", dest="en")
                        translated_text = translated_text.text
                    except Exception as e:
                        send_message(chat_id, f"Ошибка перевода: {e}")
                        continue
                    
                    # Анализируем эмоции переведенного текста
                    result = emotion_analysis(translated_text)[0]
                    emotion = result['label']
                    confidence = result['score']
                    
                    # Переводим эмоцию на русский язык
                    emotion_ru = emotion_translation.get(emotion, "неизвестная эмоция")
                    
                    # Формируем ответ
                    response = f"Эмоция: {emotion_ru}\nУверенность: {confidence:.2f}"
                    send_message(chat_id, response)
        
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
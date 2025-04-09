import telebot
from transformers import pipeline
from googletrans import Translator
from collections import defaultdict

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

# Инициализация бота
bot = telebot.TeleBot(TOKEN)

# Словарь для хранения состояний пользователей
user_states = {}

# Словарь для хранения сообщений пользователей
user_messages = defaultdict(list)

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_message = (
        "👋 Привет! Я бот для анализа ментального здоровья и давления. "
        "Отправьте мне текст (например, свои мысли или чувства), "
        "и я помогу проанализировать его эмоциональную окраску.\n"
        "Для анализа давления используйте команду /dawlenie\n"
        "Для анализа стресса используйте команду /stress\n"
        "Результаты анализа не являются диагнозом и не заменяют профессиональную помощь."
    )
    bot.reply_to(message, welcome_message)

# Команда /dawlenie
@bot.message_handler(commands=['dawlenie'])
def start_pressure_analysis(message):
    chat_id = message.chat.id
    user_states[chat_id] = "awaiting_pressure_data"
    bot.reply_to(message, "Введите ваш возраст, систолическое и диастолическое давление через пробел, например: 30 120 80")

# Команда /stress
@bot.message_handler(commands=['stress'])
def start_stress_analysis(message):
    chat_id = message.chat.id
    user_states[chat_id] = "awaiting_stress_messages"
    user_messages[chat_id].clear()
    bot.reply_to(message, "Пожалуйста, отправьте мне 5 сообщений о своих мыслях и чувствах для анализа стресса.")

# Обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    chat_id = message.chat.id
    user_text = message.text.strip()
    
    if chat_id in user_states:
        state = user_states[chat_id]
        
        if state == "awaiting_pressure_data":
            parts = user_text.split()
            if len(parts) != 3:
                bot.reply_to(message, "Введите корректные числовые значения для возраста, систолического и диастолического давления через пробел.")
                return
            
            try:
                age = int(parts[0])
                systolic = int(parts[1])
                diastolic = int(parts[2])
                result = analyze_pressure_by_age(age, systolic, diastolic)
                bot.reply_to(message, result)
                del user_states[chat_id]
            except ValueError:
                bot.reply_to(message, "Введите корректные числовые значения для возраста, систолического и диастолического давления.")
            return
        
        if state == "awaiting_stress_messages":
            if not user_text:
                bot.reply_to(message, "Пожалуйста, отправьте текст для анализа.")
                return
            
            # Переводим текст на английский
            try:
                translated_text = translator.translate(user_text, src="ru", dest="en").text
            except Exception as e:
                bot.reply_to(message, f"Ошибка перевода: {e}")
                return
            
            # Анализируем эмоции переведенного текста
            result = emotion_analysis(translated_text)[0]
            emotion = result['label']
            
            # Сохраняем эмоцию
            user_messages[chat_id].append(emotion)
            
            if len(user_messages[chat_id]) >= 5:
                stress_result = analyze_stress(user_messages[chat_id])
                bot.reply_to(message, stress_result)
                del user_states[chat_id]
                user_messages[chat_id].clear()
            else:
                remaining = 5 - len(user_messages[chat_id])
                bot.reply_to(message, f"Осталось отправить {remaining} сообщений.")
            return
    
    if not user_text:
        bot.reply_to(message, "Пожалуйста, отправьте текст для анализа.")
        return
    
    # Переводим текст на английский
    try:
        translated_text = translator.translate(user_text, src="ru", dest="en").text
    except Exception as e:
        bot.reply_to(message, f"Ошибка перевода: {e}")
        return
    
    # Анализируем эмоции переведенного текста
    result = emotion_analysis(translated_text)[0]
    emotion = result['label']
    confidence = result['score']
    
    # Переводим эмоцию на русский язык
    emotion_ru = emotion_translation.get(emotion, "неизвестная эмоция")

    # Формируем ответ
    response = f"По данному сообщению вы испытываете эмоцию: {emotion_ru}\nМоя уверенность в точности ответа: {confidence:.2f}"
    bot.reply_to(message, response)

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

# Функция для анализа стресса на основе эмоций
def analyze_stress(emotions):
    emotion_count = defaultdict(int)
    
    for emotion in emotions:
        emotion_count[emotion] += 1
    
    total_messages = len(emotions)
    stress_score = 0
    
    # Определяем веса для эмоций, связанных со стрессом
    stress_emotions = {
        "anger": 1.5,
        "annoyance": 1.2,
        "disappointment": 1.1,
        "disapproval": 1.1,
        "disgust": 1.2,
        "embarrassment": 1.0,
        "fear": 1.8,
        "grief": 1.5,
        "nervousness": 1.3,
        "sadness": 1.2,
        "stress": 2.0  # Можно добавить специальную категорию "stress", если есть такая метка в модели
    }
    
    for emotion, count in emotion_count.items():
        if emotion in stress_emotions:
            stress_score += count * stress_emotions[emotion]
    
    stress_level = stress_score / total_messages
    
    if stress_level < 0.5:
        stress_result = "Уровень стресса низкий."
    elif 0.5 <= stress_level < 1.0:
        stress_result = "Уровень стресса средний."
    else:
        stress_result = "Уровень стресса высокий. Рекомендуется обратиться к профессиональному психологу."
    
    return stress_result

# Запуск бота
if __name__ == "__main__":
    print("Бот запущен...")
    bot.polling(none_stop=True)
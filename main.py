import telebot
from transformers import pipeline
from googletrans import Translator
from collections import defaultdict

# Инициализация модели для анализа эмоций
emotion_analysis = pipeline("text-classification", model="SamLowe/roberta-base-go_emotions")

# Словарь перевода эмоций на русский язык
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

# Токен бота
TOKEN = "7903635056:AAHXpZ-VHzJY2C63q_UvrnIIDIpShfpG5FY"

# Создание экземпляра бота
bot = telebot.TeleBot(TOKEN)

# Словари для отслеживания состояний пользователей
user_states = {}
user_messages = defaultdict(list)


# Функция для создания меню
def create_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        telebot.types.KeyboardButton("/start"),
        telebot.types.KeyboardButton("/dawlenie"),
        telebot.types.KeyboardButton("/stress"),
        telebot.types.KeyboardButton("/help")
    )
    return markup


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_message = (
        "👋 Привет! Я бот для анализа ментального здоровья и давления. "
        "Используйте меню ниже для навигации.\n\n"
        "/dawlenie — Проанализировать давление\n"
        "/stress — Проанализировать уровень стресса\n"
        "/help — Получить справку о командах"
    )
    bot.reply_to(message, welcome_message, reply_markup=create_menu())


# Обработчик команды /dawlenie
@bot.message_handler(commands=['dawlenie'])
def start_pressure_analysis(message):
    chat_id = message.chat.id
    user_states[chat_id] = "awaiting_pressure_data"
    bot.reply_to(message, "Введите ваш возраст, систолическое и диастолическое давление через пробел, например: 30 120 80")


# Обработчик команды /stress
@bot.message_handler(commands=['stress'])
def start_stress_analysis(message):
    chat_id = message.chat.id
    user_states[chat_id] = "awaiting_stress_messages"
    user_messages[chat_id].clear()
    bot.reply_to(message, "Пожалуйста, отправьте мне 5 сообщений о своих мыслях и чувствах для анализа стресса.")


# Обработчик команды /help
@bot.message_handler(commands=['help'])
def send_help(message):
    help_message = (
        "📚 Список доступных команд:\n"
        "/start — Начать работу с ботом\n"
        "/dawlenie — Проанализировать давление\n"
        "/stress — Проанализировать уровень стресса\n"
        "/help — Получить справку о командах\n\n"
        "📝 Для анализа давления введите возраст, систолическое и диастолическое давление через пробел.\n"
        "💭 Для анализа стресса отправьте 5 сообщений с описанием своих мыслей и чувств."
    )
    bot.reply_to(message, help_message)


# Основной обработчик сообщений
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    chat_id = message.chat.id
    user_text = message.text.strip()
    
    if chat_id in user_states:
        state = user_states[chat_id]
        
        # Обработка данных для анализа давления
        if state == "awaiting_pressure_data":
            parts = user_text.split()
            if len(parts) != 3:
                bot.reply_to(message, "Ошибка: Введите три числа через пробел (возраст, систолическое, диастолическое).")
                return
            
            try:
                age = int(parts[0])
                systolic = int(parts[1])
                diastolic = int(parts[2])
                
                # Проверка на отрицательные значения
                if age < 0 or systolic < 0 or diastolic < 0:
                    raise ValueError("Значения не могут быть отрицательными.")
                
                result = analyze_pressure_by_age(age, systolic, diastolic)
                bot.reply_to(message, result, reply_markup=create_menu())
                del user_states[chat_id]
            except ValueError as e:
                bot.reply_to(message, f"Ошибка: {e}")
            return
        
        # Обработка данных для анализа стресса
        if state == "awaiting_stress_messages":
            if not user_text:
                bot.reply_to(message, "Пожалуйста, отправьте текст для анализа.")
                return
            
            try:
                translated_text = translator.translate(user_text, src="ru", dest="en").text
            except Exception as e:
                bot.reply_to(message, f"Ошибка перевода: {e}")
                return
            
            result = emotion_analysis(translated_text)[0]
            emotion = result['label']
            
            user_messages[chat_id].append(emotion)
            
            if len(user_messages[chat_id]) >= 5:
                stress_result = analyze_stress(user_messages[chat_id])
                bot.reply_to(message, stress_result, reply_markup=create_menu())
                del user_states[chat_id]
                user_messages[chat_id].clear()
            else:
                remaining = 5 - len(user_messages[chat_id])
                bot.reply_to(message, f"Осталось отправить {remaining} сообщений.")
            return
    
    # Анализ эмоций для обычных сообщений
    if not user_text:
        bot.reply_to(message, "Пожалуйста, отправьте текст для анализа.")
        return
    
    try:
        translated_text = translator.translate(user_text, src="ru", dest="en").text
    except Exception as e:
        bot.reply_to(message, f"Ошибка перевода: {e}")
        return
    
    result = emotion_analysis(translated_text)[0]
    emotion = result['label']
    confidence = result['score']
    
    emotion_ru = emotion_translation.get(emotion, "неизвестная эмоция")
    response = f"По данному сообщению вы испытываете эмоцию: {emotion_ru}\nМоя уверенность в точности ответа: {confidence:.2f}"
    bot.reply_to(message, response)


# Функция анализа давления
def analyze_pressure_by_age(age, systolic, diastolic):
    # Определение нормального диапазона для каждого возраста
    if age < 18:
        normal_range = (90, 120, 60, 80)  
    elif 18 <= age < 30:
        normal_range = (90, 120, 60, 80)
    elif 30 <= age < 40:
        normal_range = (90, 130, 60, 85)
    elif 40 <= age < 50:
        normal_range = (90, 140, 60, 90)
    elif 50 <= age < 60:
        normal_range = (100, 150, 70, 95)
    elif 60 <= age < 70:
        normal_range = (110, 160, 70, 100)
    else:
        normal_range = (110, 170, 70, 105)
    
    systolic_min, systolic_max, diastolic_min, diastolic_max = normal_range

    # Анализ систолического давления
    if systolic > systolic_max:
        if systolic <= systolic_max + 10:
            systolic_status = "Легкая гипертония"
        elif systolic <= systolic_max + 20:
            systolic_status = "Умеренная гипертония"
        else:
            systolic_status = "Тяжелая гипертония"
    elif systolic < systolic_min:
        if systolic >= systolic_min - 10:
            systolic_status = "Легкая гипотония"
        else:
            systolic_status = "Сильная гипотония"
    else:
        systolic_status = "Норма"

    # Анализ диастолического давления
    if diastolic > diastolic_max:
        if diastolic <= diastolic_max + 5:
            diastolic_status = "Легкая гипертония"
        elif diastolic <= diastolic_max + 10:
            diastolic_status = "Умеренная гипертония"
        else:
            diastolic_status = "Тяжелая гипертония"
    elif diastolic < diastolic_min:
        if diastolic >= diastolic_min - 5:
            diastolic_status = "Легкая гипотония"
        else:
            diastolic_status = "Сильная гипотония"
    else:
        diastolic_status = "Норма"

    # Формирование результата
    result = (
        f"Анализ давления для вашего возраста ({age}):\n"
        f"Систолическое давление: {systolic} мм рт. ст. — {systolic_status}\n"
        f"Диастолическое давление: {diastolic} мм рт. ст. — {diastolic_status}"
    )
    return result


# Функция анализа стресса
def analyze_stress(emotions):
    emotion_count = defaultdict(int)
    
    for emotion in emotions:
        emotion_count[emotion] += 1
    
    total_messages = len(emotions)
    stress_score = 0
    
    # Коэффициенты для стрессовых эмоций
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
        "stress": 2.0  
    }
    
    for emotion, count in emotion_count.items():
        if emotion in stress_emotions:
            stress_score += count * stress_emotions[emotion]
    
    stress_level = stress_score / total_messages
    
    # Определение уровня стресса
    if stress_level < 0.5:
        stress_result = "Уровень стресса низкий."
    elif 0.5 <= stress_level < 1.0:
        stress_result = "Уровень стресса средний."
    else:
        stress_result = "Уровень стресса высокий. Рекомендуется обратиться к профессиональному психологу."
    
    # Добавление информации о доминирующих эмоциях
    dominant_emotions = sorted(emotion_count.items(), key=lambda x: x[1], reverse=True)[:3]
    dominant_emotions_ru = ", ".join([f"{emotion_translation.get(e, e)} ({count})" for e, count in dominant_emotions])
    
    stress_result += f"\n\nДоминирующие эмоции: {dominant_emotions_ru}"
    return stress_result


# Запуск бота
if __name__ == "__main__":
    print("Бот запущен...")
    bot.polling(none_stop=True)
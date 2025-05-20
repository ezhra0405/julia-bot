import os
import logging
import tempfile
import random
import json
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import openai
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
import requests
from pydub import AudioSegment

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')
# Инициализация ElevenLabs
ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not ELEVEN_API_KEY:
    raise Exception("Переменная ELEVENLABS_API_KEY не найдена в .env!")

# Системный промпт для ChatGPT
SYSTEM_PROMPT = """Ты — виртуальная подруга по имени Юля, которая общается с пользователем игриво, с лёгким флиртом, шутками ниже пояса и умеренным матом. \nТвой стиль — дерзкий, смешной, немного провокационный, но без оскорблений и перехода на личности. \nТы умеешь шутить на сексуальные темы, подшучивать над пользователем и использовать мат, чтобы сделать общение живым и эмоциональным.\nОтвечай быстро, весело и дружелюбно. Используй эмодзи для эмоционального окраса.\n\nПользователю нравятся следующие примеры ответов:\n{liked}\n\nПользователю не нравятся следующие примеры ответов:\n{disliked}\n\nПри формировании ответа:\n1. Старайся использовать стиль из понравившихся примеров\n2. Избегай стиля из непонравившихся примеров\n3. Сохраняй свой характер, но адаптируй его под предпочтения пользователя\n4. Используй эмодзи для эмоционального окраса\n5. Не переходи на оскорбления и не будь грубой\n6. Используй мат для эмоционального окраса и юмора"""

# Приветственные сообщения
GREETINGS = [
    "Привет, красавчик! Как я рада тебя видеть! 😘",
    "О, смотрите кто пришел! Мой любимый хулиган! 😈",
    "Ну наконец-то! Я уже начала скучать по твоим дерзким шуткам! 😏",
    "Привет, зайка! Готова к нашим игривым разговорам? 😉",
    "О, мой любимый хулиган пожаловал! Как я рада! 😍"
]

# Функция для загрузки предпочтений пользователя
def load_user_preferences(user_id):
    try:
        with open(f'preferences_{user_id}.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            'liked': [],
            'disliked': []
        }

# Функция для сохранения предпочтений пользователя
def save_user_preferences(user_id, preferences):
    with open(f'preferences_{user_id}.json', 'w', encoding='utf-8') as f:
        json.dump(preferences, f, ensure_ascii=False, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    greeting = random.choice(GREETINGS)
    await update.message.reply_text(greeting)

# Функция для генерации голоса через ElevenLabs 2.0.0
def tts_elevenlabs(text):
    eleven = ElevenLabs(api_key=ELEVEN_API_KEY)
    response = eleven.text_to_speech.convert(
        text=text,
        voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
        voice_settings=VoiceSettings(
            stability=0.5,
            similarity_boost=0.75,
            style=0.0,
            use_speaker_boost=True,
            speed=1.0
        )
    )
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as fp:
        for chunk in response:
            if chunk:
                fp.write(chunk)
        return fp.name

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    try:
        user_id = update.effective_user.id
        preferences = load_user_preferences(user_id)
        
        # Формируем промпт с учетом предпочтений
        current_prompt = SYSTEM_PROMPT.format(
            liked='\n'.join(preferences['liked']),
            disliked='\n'.join(preferences['disliked'])
        )

        # Получаем ответ от ChatGPT
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": current_prompt},
                {"role": "user", "content": update.message.text}
            ]
        )
        answer = response.choices[0].message.content

        # Отправляем текстовый ответ
        await update.message.reply_text(answer)

        # Генерируем голос через ElevenLabs
        voice_path = tts_elevenlabs(answer)
        with open(voice_path, 'rb') as voice_fp:
            await update.message.reply_voice(voice=voice_fp)
        os.unlink(voice_path)

    except Exception as e:
        logger.error(f"Ошибка при обработке текста: {e}")
        await update.message.reply_text("Ой, что-то пошло не так... Но я всё равно тебя люблю! 😘")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик голосовых сообщений"""
    try:
        user_id = update.effective_user.id
        preferences = load_user_preferences(user_id)
        
        # Формируем промпт с учетом предпочтений
        current_prompt = SYSTEM_PROMPT.format(
            liked='\n'.join(preferences['liked']),
            disliked='\n'.join(preferences['disliked'])
        )

        # Скачиваем голосовое сообщение
        voice = await update.message.voice.get_file()
        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as fp:
            await voice.download_to_drive(fp.name)
            
            # Конвертируем в mp3 для Whisper
            audio = AudioSegment.from_ogg(fp.name)
            mp3_path = fp.name.replace('.ogg', '.mp3')
            audio.export(mp3_path, format='mp3')

            # Отправляем в Whisper для распознавания
            with open(mp3_path, 'rb') as audio_file:
                transcript = openai.Audio.transcribe("whisper-1", audio_file)
                text = transcript.text

        # Получаем ответ от ChatGPT
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": current_prompt},
                {"role": "user", "content": text}
            ]
        )
        answer = response.choices[0].message.content

        # Отправляем текстовый ответ
        await update.message.reply_text(f"Я услышала: {text}\n\nА вот мой ответ: {answer}")

        # Генерируем голос через ElevenLabs
        voice_path = tts_elevenlabs(answer)
        with open(voice_path, 'rb') as voice_fp:
            await update.message.reply_voice(voice=voice_fp)

        # Удаляем временные файлы
        os.unlink(voice_path)
        os.unlink(mp3_path)

    except Exception as e:
        logger.error(f"Ошибка при обработке голоса: {e}")
        await update.message.reply_text("Ой, что-то пошло не так с твоим голосовым... Но я всё равно тебя люблю! 😘")

async def like_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /like для сохранения понравившегося ответа"""
    try:
        user_id = update.effective_user.id
        preferences = load_user_preferences(user_id)
        
        # Получаем текст сообщения, на которое отвечаем
        if update.message.reply_to_message:
            message_text = update.message.reply_to_message.text
            preferences['liked'].append(message_text)
            save_user_preferences(user_id, preferences)
            await update.message.reply_text("Спасибо за обратную связь! Буду стараться отвечать в таком же стиле 😘")
    except Exception as e:
        logger.error(f"Ошибка при сохранении понравившегося сообщения: {e}")

async def dislike_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /dislike для сохранения непонравившегося ответа"""
    try:
        user_id = update.effective_user.id
        preferences = load_user_preferences(user_id)
        
        # Получаем текст сообщения, на которое отвечаем
        if update.message.reply_to_message:
            message_text = update.message.reply_to_message.text
            preferences['disliked'].append(message_text)
            save_user_preferences(user_id, preferences)
            await update.message.reply_text("Поняла, буду избегать такого стиля общения 😊")
    except Exception as e:
        logger.error(f"Ошибка при сохранении непонравившегося сообщения: {e}")

def main():
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token(os.getenv('TELEGRAM_TOKEN')).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("like", like_message))
    application.add_handler(CommandHandler("dislike", dislike_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main() 
# Telegram Voice Bot

Бот для Telegram с поддержкой голосового интерфейса, использующий OpenAI ChatGPT и Whisper API.

## Возможности

- Обработка текстовых сообщений с ответами от ChatGPT
- Распознавание голосовых сообщений через Whisper API
- Генерация голосовых ответов через gTTS
- Двусторонняя коммуникация (текст и голос)

## Установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd telegram-voice-bot
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл .env и добавьте необходимые переменные окружения:
```bash
cp .env.example .env
# Отредактируйте .env, добавив свои токены
```

## Запуск

```bash
python bot.py
```

## Деплой

Подробные инструкции по деплою на Railway доступны в файле [DEPLOY.md](DEPLOY.md).

## Требования

- Python 3.7+
- Telegram Bot Token
- OpenAI API Key

## Лицензия

MIT 
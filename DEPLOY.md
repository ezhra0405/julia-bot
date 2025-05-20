# Инструкция по деплою бота на Railway

## Подготовка

1. Создайте аккаунт на [Railway](https://railway.app/)
2. Установите [Railway CLI](https://docs.railway.app/develop/cli)
3. Получите токены:
   - Telegram Bot Token от [@BotFather](https://t.me/BotFather)
   - OpenAI API Key с [OpenAI Dashboard](https://platform.openai.com/api-keys)

## Деплой

1. Создайте новый проект на Railway:
```bash
railway init
```

2. Добавьте переменные окружения в Railway:
   - `TELEGRAM_TOKEN` - токен вашего Telegram бота
   - `OPENAI_API_KEY` - ваш ключ API OpenAI

3. Загрузите код:
```bash
railway up
```

## Проверка

1. После успешного деплоя, Railway предоставит URL для вашего приложения
2. Откройте бота в Telegram и отправьте команду `/start`
3. Проверьте работу с текстовыми и голосовыми сообщениями

## Мониторинг

- Логи доступны в панели управления Railway
- Настройте уведомления о сбоях в Railway Dashboard

## Обновление

Для обновления бота просто загрузите новые изменения:
```bash
railway up
``` 
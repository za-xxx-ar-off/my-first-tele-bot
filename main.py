import logging
import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# === НАСТРОЙКИ (через переменные окружения) ===
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
BASE_ID = os.getenv("BASE_ID")
TABLE_NAME = os.getenv("TABLE_NAME", "Photos")  # по умолчанию "Photos"

# === ЛОГГИРОВАНИЕ ===
logging.basicConfig(level=logging.INFO)

# === ФУНКЦИЯ ПОЛУЧЕНИЯ ДАННЫХ ИЗ AIRTABLE ===
def fetch_airtable_photos():
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    data = response.json()

    photos = []
    for record in data.get('records', []):
        fields = record.get('fields', {})
        name = fields.get('Name')
        photo_url = fields.get('Photo URL')
        if name and photo_url:
            photos.append((name, photo_url))
    return photos

# === ОБРАБОТЧИК /photos ===
async def send_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photos = fetch_airtable_photos()
    if not photos:
        await update.message.reply_text("Фотографии не найдены.")
        return

    for name, photo_url in photos:
        try:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=photo_url,
                caption=name
            )
        except Exception as e:
            logging.error(f"Ошибка при отправке {name}: {e}")
            await update.message.reply_text(f"Не удалось отправить фото: {name}")

    await update.message.reply_text("Готово ✅")

# === ГЛАВНАЯ ФУНКЦИЯ ===
def main():
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("❌ BOT_TOKEN не найден. Задай переменные окружения в Render.")
    if not AIRTABLE_TOKEN or not BASE_ID:
        raise ValueError("❌ AIRTABLE_TOKEN и BASE_ID должны быть заданы в переменных окружения.")

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("photos", send_photos))

    logging.info("🤖 Бот запущен. Ожидает команды /photos ...")
    app.run_polling()

if __name__ == '__main__':
    main()

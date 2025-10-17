import logging
import os
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# === Настройки ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
BASE_ID = os.getenv("BASE_ID")
TABLE_NAME = os.getenv("TABLE_NAME", "Photos")

# === Логирование ===
logging.basicConfig(level=logging.INFO)

# === Flask ===
app = Flask(__name__)

# === Инициализация Telegram приложения ===
telegram_app = Application.builder().token(BOT_TOKEN).build()

# === Получение данных из Airtable ===
def fetch_airtable_photos():
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
    headers = {"Authorization": f"Bearer {AIRTABLE_TOKEN}", "Content-Type": "application/json"}
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
    except Exception as e:
        logging.error(f"Ошибка при запросе к Airtable: {e}")
        return []

    photos = []
    for record in data.get("records", []):
        fields = record.get("fields", {})
        name = fields.get("Name")
        photo_url = fields.get("Photo URL")
        if name and photo_url:
            photos.append((name, photo_url))
    return photos

# === Обработчик /photos ===
async def send_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photos = fetch_airtable_photos()
    if not photos:
        await update.message.reply_text("Фотографии не найдены.")
        return

    for name, photo_url in photos[:10]:  # первые 10 фото
        try:
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo_url, caption=name)
        except Exception as e:
            logging.error(f"Ошибка при отправке {name}: {e}")

    await update.message.reply_text("Готово ✅")

telegram_app.add_handler(CommandHandler("photos", send_photos))

# === Flask route для Telegram webhook ===
@app.route("/webhook", methods=["POST"])
def webhook():
    """Получает обновления от Telegram"""
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    telegram_app.update_queue.put_nowait(update)
    return "ok", 200

# === Проверочный маршрут ===
@app.route("/")
def home():
    return "✅ Telegram Bot is running on Render via Webhook!"

# === Установка webhook при запуске ===
def set_webhook():
    webhook_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/webhook"
    telegram_app.bot.set_webhook(url=webhook_url)
    logging.info(f"🌐 Webhook установлен: {webhook_url}")

# === Точка входа ===
if __name__ == "__main__":
    set_webhook()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

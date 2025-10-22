import logging
import os
import requests
import asyncio
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
logger = logging.getLogger(__name__)

# === Flask ===
app = Flask(__name__)

# === Telegram bot ===
telegram_app = Application.builder().token(BOT_TOKEN).build()

# === Получаем фото из Airtable ===
def fetch_airtable_photos():
    try:
        url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
        headers = {"Authorization": f"Bearer {AIRTABLE_TOKEN}"}
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        data = r.json()
        photos = []
        for record in data.get("records", []):
            f = record.get("fields", {})
            if "Name" in f and "Photo URL" in f:
                photos.append((f["Name"], f["Photo URL"]))
        return photos
    except Exception as e:
        logger.error(f"Airtable fetch error: {e}")
        return []

# === Команда /photos ===
async def send_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Received /photos command")
    photos = fetch_airtable_photos()
    if not photos:
        await update.message.reply_text("Фотографии не найдены.")
        return
    for name, url in photos:
        try:
            await update.message.reply_photo(photo=url, caption=name)
        except Exception as e:
            logger.error(f"Error sending photo {name}: {e}")
    await update.message.reply_text("Готово ✅")

telegram_app.add_handler(CommandHandler("photos", send_photos))

# === Flask маршруты ===
@app.route("/")
def home():
    return "✅ Bot is running!"

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        logger.info(f"Incoming update: {data}")
        update = Update.de_json(data, telegram_app.bot)
        asyncio.run(process_update_async(update))
    except Exception as e:
        logger.error(f"Webhook processing error: {e}", exc_info=True)
    return "ok"

# === Асинхронная обработка апдейта ===
async def process_update_async(update: Update):
    await telegram_app.initialize()
    await telegram_app.process_update(update)
    await telegram_app.shutdown()

# === Устанавливаем Webhook ===
def set_webhook():
    url = f"https://my-first-tele-bot.onrender.com/{BOT_TOKEN}"
    set_hook = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={url}")
    logger.info(f"Webhook set: {set_hook.text}")

if __name__ == "__main__":
    set_webhook()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

import logging
import os
import requests
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# === НАСТРОЙКИ ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
BASE_ID = os.getenv("BASE_ID")
TABLE_NAME = os.getenv("TABLE_NAME", "Photos")

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

# === Telegram bot initialization ===
telegram_app = Application.builder().token(BOT_TOKEN).build()

# === Функция получения данных из Airtable ===
def fetch_airtable_photos():
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
    headers = {"Authorization": f"Bearer {AIRTABLE_TOKEN}"}
    response = requests.get(url, headers=headers)
    data = response.json()
    photos = []
    for record in data.get("records", []):
        fields = record.get("fields", {})
        if "Name" in fields and "Photo URL" in fields:
            photos.append((fields["Name"], fields["Photo URL"]))
    return photos

# === Команда /photos ===
async def send_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photos = fetch_airtable_photos()
    if not photos:
        await update.message.reply_text("Фотографии не найдены.")
        return
    for name, url in photos[:10]:  # ограничим 10 фото
        await update.message.reply_photo(photo=url, caption=name)
    await update.message.reply_text("Готово ✅")

telegram_app.add_handler(CommandHandler("photos", send_photos))

# === Flask endpoints ===
@app.route("/")
def home():
    return "✅ Bot is running on Render!"

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, telegram_app.bot)
    asyncio.run(telegram_app.process_update(update))
    return "ok"

# === Установка webhook при запуске ===
def set_webhook():
    url = f"https://my-first-tele-bot.onrender.com/{BOT_TOKEN}"
    set_hook = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={url}")
    logging.info(f"Webhook set: {set_hook.text}")

# === Запуск ===
if __name__ == "__main__":
    set_webhook()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

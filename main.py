import os
import logging
import requests
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Настройки ---
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = "photos"  # или "фотографии", если так называется таблица
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Flask(__name__)
telegram_app = Application.builder().token(BOT_TOKEN).build()

logging.basicConfig(level=logging.INFO)


# --- Получение фото из Airtable ---
def get_photos_from_airtable():
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
    response = requests.get(url, headers=headers)
    data = response.json()

    photos = []

    for record in data.get("records", []):
        fields = record.get("fields", {})
        name = fields.get("Name") or fields.get("Название")  # поддержка русского варианта

        # Берём фото из поля Attachments
        attachments = (
            fields.get("Photo") or
            fields.get("Photos") or
            fields.get("Фото") or
            fields.get("Attachments")
        )

        if attachments and isinstance(attachments, list):
            photo_url = attachments[0].get("url")
            if name and photo_url:
                photos.append((name, photo_url))

    return photos


# --- Обработка команд ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Напиши 'фото', чтобы увидеть мебель 😊")


async def send_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photos = get_photos_from_airtable()

    if not photos:
        await update.message.reply_text("❌ Фотографии не найдены в Airtable.")
        return

    for name, photo_url in photos:
        try:
            await update.message.reply_photo(photo=photo_url, caption=name)
        except Exception as e:
            logging.error(f"Ошибка при отправке фото {name}: {e}")


# --- Настройка хендлеров ---
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_photos))


# --- Webhook Flask ---
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    telegram_app.update_queue.put_nowait(update)
    return "ok"


if __name__ == "__main__":
    telegram_app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        url_path=BOT_TOKEN,
        webhook_url=f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/{BOT_TOKEN}"
    )

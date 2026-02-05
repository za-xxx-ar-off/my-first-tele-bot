import logging
from typing import Dict, List

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

import db
import sheets

# -------------------------------------------------
# CONFIG (можно без env)
# -------------------------------------------------
BOT_TOKEN = "PASTE_BOT_TOKEN_HERE"
ADMIN_USER_ID = 123456789  # TODO: замените на ваш Telegram user_id

PAYMENT_INFO_TEXT = (
    "💳 Оплата курсов\n"
    "Humo / Uzcard\n"
    "Карта: XXXX XXXX XXXX XXXX\n"
    "Получатель: ФИО\n\n"
    "После оплаты нажмите «Я оплатил», и мы подтвердим платеж."
)

TRIAL_LESSON_TEXT = (
    "🎬 Пробный урок\n"
    "Посмотри видео ниже прямо в Telegram."
)
TRIAL_LESSON_URL = "https://youtu.be/dQw4w9WgXcQ"

# -------------------------------------------------
# LOGGING
# -------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------------------------
# KEYBOARDS
# -------------------------------------------------
PAYMENT_KEYBOARD = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("💳 Оплата (инструкция)", callback_data="payment_info")],
        [InlineKeyboardButton("✅ Я оплатил", callback_data="payment_done")],
    ]
)


def build_test_keyboard(options: List[str]) -> InlineKeyboardMarkup:
    buttons = []
    for index, option in enumerate(options, start=1):
        buttons.append(
            [InlineKeyboardButton(option, callback_data=f"answer:{index}")]
        )
    return InlineKeyboardMarkup(buttons)


def build_next_stage_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🧪 Начать тест", callback_data="start_test")]]
    )


# -------------------------------------------------
# HELPERS
# -------------------------------------------------
async def send_stage_videos(chat_id: int, stage_index: int, context: ContextTypes.DEFAULT_TYPE):
    stage = sheets.get_stage(stage_index)
    if stage is None:
        return

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"📚 Этап {stage_index + 1}: {stage['title']}",
    )
    for video in stage["videos"]:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"▶️ {video['title']}\n{video['url']}",
            disable_web_page_preview=False,
        )
    await context.bot.send_message(
        chat_id=chat_id,
        text="Когда будешь готов, начинай тест 👇",
        reply_markup=build_next_stage_keyboard(),
    )


async def send_question(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    state = db.get_state(chat_id)
    stage = sheets.get_stage(state["stage"])
    if stage is None:
        return
    question = sheets.get_question(state["stage"], state["question"])
    if question is None:
        return
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"❓ Вопрос {state['question'] + 1}: {question['text']}",
        reply_markup=build_test_keyboard(question["options"]),
    )


async def finish_stage(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    state = db.get_state(chat_id)
    next_stage = state["stage"] + 1
    if next_stage >= sheets.get_stage_count():
        await context.bot.send_message(
            chat_id=chat_id,
            text="🎉 Поздравляем! Ты прошёл все этапы.",
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text="📨 Мы получили твою заявку. Скоро свяжемся!",
        )
        await notify_admin_completion(chat_id, context)
        db.reset_state(chat_id)
        return

    db.set_stage(chat_id, next_stage)
    await context.bot.send_message(
        chat_id=chat_id,
        text="✅ Тест завершён! Переходим к следующему этапу.",
    )
    await send_stage_videos(chat_id, next_stage, context)


async def notify_admin_payment(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    if ADMIN_USER_ID == 123456789:
        return
    await context.bot.send_message(
        chat_id=ADMIN_USER_ID,
        text=(
            "💸 Клиент сообщил об оплате.\n"
            f"User ID: {chat_id}\n"
            "Подтвердить: /confirm <user_id>"
        ),
    )


async def notify_admin_completion(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    if ADMIN_USER_ID == 123456789:
        return
    await context.bot.send_message(
        chat_id=ADMIN_USER_ID,
        text=f"✅ Клиент прошёл все этапы. User ID: {chat_id}",
    )


# -------------------------------------------------
# HANDLERS
# -------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    db.ensure_user(chat_id)

    await update.message.reply_text(TRIAL_LESSON_TEXT)
    await update.message.reply_text(TRIAL_LESSON_URL)
    await update.message.reply_text(
        "Чтобы продолжить обучение, нужно оплатить курс.",
        reply_markup=PAYMENT_KEYBOARD,
    )


async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("Недостаточно прав.")
        return

    if not context.args:
        await update.message.reply_text("Использование: /confirm <user_id>")
        return

    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("User ID должен быть числом.")
        return

    db.set_paid(target_id, True)
    db.set_pending(target_id, False)
    await update.message.reply_text(f"Оплата подтверждена для {target_id}.")
    await context.bot.send_message(
        chat_id=target_id,
        text="✅ Оплата подтверждена! Открываю доступ к урокам.",
    )
    await send_stage_videos(target_id, 0, context)


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    db.ensure_user(chat_id)

    if query.data == "payment_info":
        await query.message.reply_text(PAYMENT_INFO_TEXT)
        return

    if query.data == "payment_done":
        db.set_pending(chat_id, True)
        await query.message.reply_text(
            "Спасибо! Мы проверим оплату и откроем доступ.",
        )
        await notify_admin_payment(chat_id, context)
        return

    state = db.get_state(chat_id)
    if not state["paid"]:
        await query.message.reply_text(
            "Доступ к урокам откроется после подтверждения оплаты.",
        )
        return

    if query.data == "start_test":
        db.set_question(chat_id, 0)
        await send_question(chat_id, context)
        return

    if query.data.startswith("answer:"):
        answer_index = int(query.data.split(":", 1)[1])
        db.save_answer(chat_id, answer_index)
        next_question = db.advance_question(chat_id)
        if next_question is None:
            await finish_stage(chat_id, context)
            return
        await send_question(chat_id, context)
        return


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Команды:\n"
        "/start — начать\n"
        "/confirm <user_id> — подтвердить оплату (только админ)"
    )


def main() -> None:
    if BOT_TOKEN == "PASTE_BOT_TOKEN_HERE":
        logger.warning("⚠️ BOT_TOKEN не задан.")

    db.init()
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("confirm", confirm_payment))
    application.add_handler(CallbackQueryHandler(buttons))

    logger.info("🤖 Бот запущен (polling).")
    application.run_polling()


if __name__ == "__main__":
    main()

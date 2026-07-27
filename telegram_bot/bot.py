"""
Logistika Tarjimon — Telegram bot.

Ishga tushirish:
    cd logistics-translator
    python telegram_bot/bot.py

Kerakli narsa: loyiha tub papkasida (.env faylida) TELEGRAM_BOT_TOKEN
va GEMINI_API_KEY sozlangan bo'lishi kerak.
"""
import io
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# --- Yo'llarni sozlash: "core" modulini import qila olishimiz uchun ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from core import translate
from core.voice import transcribe_and_translate_audio, synthesize_speech

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


WELCOME_MESSAGE = (
    "👋 Assalomu alaykum! Men *Logistika Tarjimon* botiman.\n\n"
    "Menga o'zbekcha yoki inglizcha matn YOKI ovozli xabar yuboring — "
    "men uni logistika atamalarini hisobga olib tarjima qilib beraman.\n"
    "Ovozli xabar yuborsangiz, tarjimani ham ovozda eshitasiz!\n\n"
    "Masalan:\n"
    "🔹 \"Yukni qachon olib ketasiz?\"\n"
    "🔹 \"What's the detention rate?\"\n\n"
    "Buyruqlar:\n"
    "/start — botni qayta ishga tushirish\n"
    "/help — yordam"
)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MESSAGE, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Shunchaki menga matn yozing (o'zbekcha yoki inglizcha) — "
        "men avtomatik tilni aniqlab, tarjima qilib beraman."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    # Foydalanuvchiga "yozmoqda..." holatini ko'rsatamiz (chat action)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        result = translate(user_text)
        translated_text = result["translated_text"]
        engine = result["engine"]

        direction_label = (
            "🇺🇿 → 🇺🇸" if result["direction"] == "uz_to_en" else "🇺🇸 → 🇺🇿"
        )
        engine_label = "Gemini AI" if engine == "gemini" else "Google Tarjimon (zaxira)"

        reply = f"{direction_label}\n\n{translated_text}\n\n_({engine_label})_"
        await update.message.reply_text(reply, parse_mode="Markdown")

    except Exception as exc:
        logger.exception("Tarjima qilishda xatolik yuz berdi")
        await update.message.reply_text(
            "⚠️ Kechirasiz, tarjima qilishda xatolik yuz berdi. "
            "Birozdan so'ng qayta urinib ko'ring."
        )


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="record_voice")

    try:
        # 1. Telegram'dan ovozli xabarni yuklab olamiz (.ogg format)
        voice_file = await update.message.voice.get_file()
        audio_bytes = bytes(await voice_file.download_as_bytearray())

        # 2. Gemini orqali tilni aniqlab, tarjima qilamiz
        result = transcribe_and_translate_audio(audio_bytes, mime_type="audio/ogg")
        detected_lang = result["detected_language"]
        translated_text = result["translated_text"]
        target_lang = "en" if detected_lang == "uz" else "uz"

        # 3. Natijani ovozga aylantiramiz
        audio_out = synthesize_speech(translated_text, target_lang)

        # 4. Matn va ovozni foydalanuvchiga yuboramiz
        direction_label = "🇺🇿 → 🇺🇸" if detected_lang == "uz" else "🇺🇸 → 🇺🇿"
        await update.message.reply_text(f"{direction_label}\n\n{translated_text}")

        audio_stream = io.BytesIO(audio_out)
        audio_stream.name = "tarjima.mp3"
        await update.message.reply_audio(audio=audio_stream)

    except Exception:
        logger.exception("Ovozli xabarni qayta ishlashda xatolik yuz berdi")
        await update.message.reply_text(
            "⚠️ Kechirasiz, ovozli xabarni qayta ishlashda xatolik yuz berdi. "
            "Birozdan so'ng qayta urinib ko'ring."
        )


def main():
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN topilmadi. Loyiha tub papkasidagi .env "
            "faylida TELEGRAM_BOT_TOKEN=... qatorini sozlang."
        )

    app = Application.builder().token(bot_token).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot ishga tushdi. To'xtatish uchun Ctrl+C bosing.")
    app.run_polling()


if __name__ == "__main__":
    main()
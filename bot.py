import os
import re
import logging
from dotenv import load_dotenv

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

load_dotenv()
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # contoh: @usernamechannel
MAX_LEN = int(os.getenv("MAX_LEN", "1500"))
LINK_POLICY = os.getenv("LINK_POLICY", "allow")  # allow | block

def sanitize(text: str) -> str:
    text = text or ""
    text = text.strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text

def contains_link(text: str) -> bool:
    return bool(re.search(r"(https?://|t\.me/|www\.)", (text or "").lower()))

def format_caption(caption: str) -> str:
    caption = sanitize(caption)
    if not caption:
        return "📮 <b>Menfess</b>"
    if len(caption) > MAX_LEN:
        caption = caption[:MAX_LEN - 3] + "..."
    if LINK_POLICY == "block" and contains_link(caption):
        caption = "[caption mengandung link — ditolak]"
    return f"📮 <b>Menfess</b>\n\n{caption}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Kirim menfess kamu di sini (teks / foto / video).\n"
        "Aku akan autopost ke channel.\n\n"
        "Catatan: jangan kirim data pribadi, fitnah, atau konten kebencian ya."
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Cara pakai:\n"
        "- Kirim teks, foto, atau video ke bot via DM\n"
        "- Bot akan autopost ke channel\n\n"
        "Kalau gagal: cek bot sudah Admin channel dan CHANNEL_ID benar."
    )

async def handle_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    try:
        # FOTO
        if msg.photo:
            photo = msg.photo[-1]
            caption = format_caption(msg.caption or "")
            await context.bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=photo.file_id,
                caption=caption,
                parse_mode=ParseMode.HTML
            )
            await msg.reply_text("Terkirim ✅")
            return

        # VIDEO
        if msg.video:
            caption = format_caption(msg.caption or "")
            await context.bot.send_video(
                chat_id=CHANNEL_ID,
                video=msg.video.file_id,
                caption=caption,
                parse_mode=ParseMode.HTML
            )
            await msg.reply_text("Terkirim ✅")
            return

        # TEKS
        if msg.text:
            text = sanitize(msg.text)

            if len(text) > MAX_LEN:
                await msg.reply_text(f"Kepanjangan 😅 Maks {MAX_LEN} karakter.")
                return

            if LINK_POLICY == "block" and contains_link(text):
                await msg.reply_text("Maaf, link tidak diperbolehkan.")
                return

            post = f"📮 <b>Menfess</b>\n\n{text}"
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=post,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            await msg.reply_text("Terkirim ✅")
            return

        await msg.reply_text("Untuk saat ini aku menerima: teks, foto, atau video ya 🙂")

    except Exception:
        logging.exception("Posting failed")
        await msg.reply_text(
            "Gagal posting. Cek:\n"
            "1) Bot sudah jadi Admin di channel\n"
            "2) Bot punya izin post media\n"
            "3) CHANNEL_ID benar (mis: @namachannel)"
        )

def main():
    if not BOT_TOKEN or not CHANNEL_ID:
        raise RuntimeError("BOT_TOKEN dan CHANNEL_ID wajib di-set di environment variables.")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.ALL, handle_all))

    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

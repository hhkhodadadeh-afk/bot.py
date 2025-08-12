# telegram_instagram_youtube_bot.py
import os
import asyncio
from yt_dlp import YoutubeDL
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

TOKEN = os.getenv("TELEGRAM_TOKEN")

# پشتیبانی کیفیت‌ها
VALID_QUALITIES = ["144", "240", "360", "720", "1080"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! لینک اینستاگرام یا یوتیوب رو بفرست.\n"
                                    "مثال: \n"
                                    "`https://youtu.be/abcd1234`\n"
                                    "یا برای کیفیت خاص:\n"
                                    "`https://youtu.be/abcd1234 720`\n",
                                    parse_mode="Markdown")

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    parts = text.split()
    url = parts[0]
    quality = "360"  # پیش‌فرض

    if len(parts) > 1 and parts[1] in VALID_QUALITIES:
        quality = parts[1]

    await update.message.reply_text(f"در حال دانلود ویدیو با کیفیت {quality}p ...")

    ydl_opts = {
        "format": f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]",
        "noplaylist": True,
        "quiet": True,
        "outtmpl": "-",
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get("title", "ویدیو")
            description = info.get("description", "")
            formats = info.get("formats", [])
            best_format = None
            for f in formats:
                if f.get("height") == int(quality) and f.get("url"):
                    best_format = f
                    break
            if not best_format:
                best_format = formats[-1]  # fallback

            video_url = best_format["url"]

            await update.message.reply_video(video=video_url, caption=f"{title}\n\n{description[:1500]}")

    except Exception as e:
        await update.message.reply_text(f"خطا در دانلود: {str(e)}")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

    print("ربات روشن شد...")
    app.run_polling()

if __name__ == "__main__":
    main()

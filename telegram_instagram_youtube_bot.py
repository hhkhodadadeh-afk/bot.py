#!/usr/bin/env python3
"""
Optimized Telegram bot for downloading videos from YouTube and Instagram using yt_dlp.
- Supports qualities: 144, 240, 360 (default), 720, 1080.
- Downloads temporarily in RAM/disk, sends to Telegram, and deletes immediately.
- Protects against large file sizes and ensures cleanup even on error.

Requirements (requirements.txt):
python-telegram-bot==13.15
yt-dlp
"""

import os
import re
import logging
import tempfile
import shutil
import uuid
from pathlib import Path
from yt_dlp import YoutubeDL
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, CallbackContext

TOKEN = os.environ.get('8338273521:AAEJYhS3fLHG-qSM4LZh-na3xa42cJN-Ufk')
if not TOKEN:
    raise RuntimeError('Please set TELEGRAM_TOKEN environment variable')

SUPPORTED_QUALITIES = [144, 240, 360, 720, 1080]
DEFAULT_QUALITY = 360
MAX_FILE_SIZE_MB = 50  # Prevent sending too large files to Telegram

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_message(text: str):
    if not text:
        return None, None
    parts = text.strip().split()
    url = parts[0]
    q = DEFAULT_QUALITY
    if len(parts) > 1:
        try:
            qval = int(parts[1])
            if qval in SUPPORTED_QUALITIES:
                q = qval
        except Exception:
            pass
    return url, q

def select_format_selector(max_height: int):
    return f"bestvideo[height<={max_height}]+bestaudio/best[height<={max_height}]/best"

def download_video(url: str, quality: int, tmp_dir: Path):
    ydl_opts = {
        'outtmpl': str(tmp_dir / '%(title).200s.%(ext)s'),
        'format': select_format_selector(quality),
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
    }
    logger.info('Downloading: %s (quality<=%d)', url, quality)
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    if 'entries' in info and info['entries']:
        info = info['entries'][0]

    files = list(tmp_dir.glob('*'))
    if not files:
        raise FileNotFoundError('No downloaded file found')

    video_file = max(files, key=lambda p: p.stat().st_size)
    file_size_mb = video_file.stat().st_size / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(f'File too large ({file_size_mb:.1f} MB). Max {MAX_FILE_SIZE_MB} MB allowed.')

    return {
        'file_path': video_file,
        'description': info.get('description') or '',
        'title': info.get('title') or video_file.stem
    }

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        'سلام! لینک و کیفیت (اختیاری) رو ارسال کن.\n'
        'مثال:\nhttps://youtu.be/abcd123 720\nیا\nhttps://instagram.com/p/abcd123'
    )

def handle_message(update: Update, context: CallbackContext):
    url, quality = parse_message(update.message.text or '')
    if not url or not re.match(r'https?://', url):
        update.message.reply_text('لطفاً یک لینک معتبر ارسال کن.')
        return

    tmp_dir = Path(tempfile.gettempdir()) / f"tg_dl_{uuid.uuid4().hex}"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    processing_msg = update.message.reply_text('در حال پردازش...')
    try:
        result = download_video(url, quality, tmp_dir)
        caption = f"{result['title']}\n\n"
        if result['description']:
            caption += (result['description'][:1000] + '...') if len(result['description']) > 1000 else result['description']

        with open(result['file_path'], 'rb') as f:
            update.message.reply_video(video=f, caption=caption[:1024])

    except Exception as e:
        logger.exception('Error:')
        update.message.reply_text(f'خطا: {e}')
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        processing_msg.delete()

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    logger.info('Bot started.')
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

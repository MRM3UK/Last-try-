import os
import yt_dlp
import re
from telegram import ChatAction, ParseMode, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from keep_alive import keep_alive  # keep_alive for Render

# === CONFIG ===
TOKEN = "8057169535:AAGCzrepu_YXLrlABuV5Gdgd14yquabFJ-Y"
DOWNLOAD_DIR = "downloads"
COOKIE_FILE = "cookies.txt"
BOT_USERNAME = "@DownloaderReelbot"
LOG_CHANNEL_ID = -1002515325796

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def clean_caption(text):
    return re.sub(r'([_*`()~>#+=|{}.!\\-])', r'\\\1', text)

def build_caption(insta_username, title, caption, url):
    caption = clean_caption(caption.strip() if caption else title)
    spoiler_caption = f"||{caption}||"
    final_caption = (
        f" Video by _{insta_username}_\n\n"
        f"{spoiler_caption}\n\n"
        f"{url}\n\n"
        f"{BOT_USERNAME}"
    )
    return final_caption[:1024]

def download_video(url):
    ydl_opts = {
        'format': 'best',
        'cookiefile': COOKIE_FILE,
        'outtmpl': f"{DOWNLOAD_DIR}/%(title).40s.%(ext)s",
        'quiet': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get('title', '')
        desc = info.get('description', '') or info.get('caption', '')
        uploader = info.get('uploader', 'unknown')
        return ydl.prepare_filename(info), title, desc, uploader

def start(update: Update, context: CallbackContext):
    update.message.reply_text("👋 Welcome! Send a video link and I’ll download it!")

def handle_message(update: Update, context: CallbackContext):
    url = update.message.text.strip()
    chat = update.effective_chat
    user = update.effective_user

    context.bot.send_chat_action(chat_id=chat.id, action=ChatAction.UPLOAD_DOCUMENT)

    try:
        file_path, title, description, uploader = download_video(url)
        caption_text = build_caption(uploader, title, description, url)

        context.bot.delete_message(chat_id=chat.id, message_id=update.message.message_id)

        with open(file_path, 'rb') as f:
            try:
                context.bot.send_video(
                    chat_id=chat.id,
                    video=f,
                    caption=caption_text,
                    parse_mode=ParseMode.MARKDOWN
                )
                f.seek(0)
                context.bot.send_video(
                    chat_id=LOG_CHANNEL_ID,
                    video=f,
                    caption=f"👤 {user.full_name} (@{user.username})\n\n{caption_text}",
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                f.seek(0)
                context.bot.send_document(
                    chat_id=chat.id,
                    document=f,
                    caption=caption_text[:1024],
                    parse_mode=ParseMode.MARKDOWN
                )
                f.seek(0)
                context.bot.send_document(
                    chat_id=LOG_CHANNEL_ID,
                    document=f,
                    caption=f"👤 {user.full_name} (@{user.username})\n\n{caption_text[:1024]}",
                    parse_mode=ParseMode.MARKDOWN
                )
        os.remove(file_path)
    except Exception as e:
        error_msg = f"❌ Error for {user.full_name} (@{user.username}): {str(e)}"
        update.message.reply_text(error_msg)
        context.bot.send_message(chat_id=LOG_CHANNEL_ID, text=error_msg)

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    keep_alive()
    updater.idle()

if __name__ == "__main__":
    main()

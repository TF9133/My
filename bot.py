import os
import glob
import instaloader
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# 1. 開啟影片下載功能
L = instaloader.Instaloader(
    download_videos=True,            # 改為 True 以支援 Reel / 影片
    download_video_thumbnails=False,
    download_comments=False,
    save_metadata=False
)

# 2. 載入私人帳戶 Session（將 session.txt 放在同一個資料夾）
SESSION_FILE = "session.txt"
IG_USERNAME = os.environ.get("ka.__.kit", "") # 你的 IG 帳號名稱

if os.path.exists(SESSION_FILE) and IG_USERNAME:
    try:
        L.load_session_from_file(IG_USERNAME, filename=SESSION_FILE)
        print("成功載入 IG Session！可以下載已追蹤的私人帳戶內容。")
    except Exception as e:
        print(f"Session 載入失敗：{e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("你好！請傳送 Instagram 貼文或 Reel 連結給我，我會幫你下載照片或影片。")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if "instagram.com" not in url:
        await update.message.reply_text("請提供有效的 Instagram 連結！")
        return

    status_msg = await update.message.reply_text("擷取媒體中，請稍候...")

    try:
        # 解析 Shortcode
        if "/p/" in url:
            shortcode = url.split("/p/")[1].split("/")[0]
        elif "/reel/" in url:
            shortcode = url.split("/reel/")[1].split("/")[0]
        elif "/reels/" in url:
            shortcode = url.split("/reels/")[1].split("/")[0]
        else:
            await status_msg.edit_text("無法解析該連結。")
            return

        target_dir = f"temp_{shortcode}"
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target=target_dir)

        # 3. 同時搜尋照片 (.jpg, .png, .webp) 與影片 (.mp4)
        media_files = (
            glob.glob(f"{target_dir}/*.mp4") + 
            glob.glob(f"{target_dir}/*.jpg") + 
            glob.glob(f"{target_dir}/*.png")
        )

        if not media_files:
            await status_msg.edit_text("未找到可發送的媒體檔。")
        else:
            await status_msg.edit_text(f"找到 {len(media_files)} 個檔案，傳送中...")
            for file_path in media_files:
                with open(file_path, 'rb') as f:
                    # 根據副檔名判斷發送影片定照片
                    if file_path.endswith('.mp4'):
                        await update.message.reply_video(video=f)
                    else:
                        await update.message.reply_photo(photo=f)

        # 清理臨時檔案
        for file in glob.glob(f"{target_dir}/*"):
            os.remove(file)
        os.rmdir(target_dir)

    except Exception as e:
        await status_msg.edit_text(f"處理失敗：{str(e)}\n注意：下載私人帳戶貼文需要你先成功追蹤該帳號。")

def main():
    TOKEN = os.environ.get("BOT_TOKEN")
    if not TOKEN:
        print("未設定 BOT_TOKEN！")
        return

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot 正在運行中...")
    app.run_polling()

if __name__ == '__main__':
    main()


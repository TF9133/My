import os
import glob
import instaloader
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# 初始化 Instaloader
L = instaloader.Instaloader(
    download_videos=False,      # 如果只想抓圖片可設為 False，想抓影片可改成 True
    download_video_thumbnails=False,
    download_comments=False,
    save_metadata=False
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("你好！請傳送 Instagram 貼文連結給我，我會幫你下載照片。")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if "instagram.com" not in url:
        await update.message.reply_text("請提供有效的 Instagram 貼文連結！")
        return

    status_msg = await update.message.reply_text("擷取照片中，請稍候...")

    try:
        # 從連結中解析 Shortcode
        if "/p/" in url:
            shortcode = url.split("/p/")[1].split("/")[0]
        elif "/reel/" in url:
            shortcode = url.split("/reel/")[1].split("/")[0]
        else:
            await status_msg.edit_text("無法解析該連結，請確認是否為公開貼文。")
            return

        # 建立臨時儲存資料夾
        target_dir = f"temp_{shortcode}"
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target=target_dir)

        # 搜尋下載下來的圖片檔案 (.jpg / .png / .webp)
        image_files = glob.glob(f"{target_dir}/*.jpg") + glob.glob(f"{target_dir}/*.png") + glob.glob(f"{target_dir}/*.webp")

        if not image_files:
            await status_msg.edit_text("未找到可發送的照片（可能是影片或私人帳號貼文）。")
        else:
            await status_msg.edit_text(f"找到 {len(image_files)} 張照片，傳送中...")
            for img_path in image_files:
                with open(img_path, 'rb') as photo:
                    await update.message.reply_photo(photo=photo)

        # 清理下載的臨時檔案
        for file in glob.glob(f"{target_dir}/*"):
            os.remove(file)
        os.rmdir(target_dir)

    except Exception as e:
        await status_msg.edit_text(f"處理失敗：{str(e)}\n注意：公開貼文才能成功下載。")

def main():
    # 替換為你的 Telegram Bot Token
    TOKEN = '8843707608:AAHnXnzocUMns6xZyDTx1kT3Qo8W9ykcmy8'

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot 正在運行中...")
    app.run_polling()

if __name__ == '__main__':
    main()

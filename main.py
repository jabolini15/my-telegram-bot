import os
import requests
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

SYSTEM_PROMPT = (
    "تو یک دستیار هوشمند، بسیار باهوش، رفیق و صمیمی هستی. "
    "همیشه به زبان فارسی روان، اصیل، جذاب و طبیعی صحبت کن. "
    "اصلاً از لحن خشک، اداری یا ترجمه‌های کتابی و ماشینی استفاده نکن. "
    "توی صحبت‌هات خیلی راحت، گرم و انرژی‌بخش باش و از ایموجی‌های مناسب استفاده کن 😊😉."
)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    user_text = update.message.text
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    
    payload = {
        "system_instruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "contents": [
            {"parts": [{"text": user_text}]}
        ],
        "generationConfig": {
            "temperature": 0.7
        }
    }
    
    try:
        res = requests.post(url, json=payload, timeout=30)
        data = res.json()
        
        if res.status_code == 200 and "candidates" in data:
            reply = data["candidates"][0]["content"]["parts"][0]["text"]
            await update.message.reply_text(reply)
        else:
            error_msg = data.get("error", {}).get("message", "خطای غیرمنتظره در API")
            await update.message.reply_text(f"خطا در API جمینی: {error_msg}")
            
    except Exception as e:
        await update.message.reply_text(f"خطا در ارتباط: {str(e)}")

async def main():
    if not BOT_TOKEN or not GEMINI_KEY:
        print("خطا: متغیرهای محیطی TELEGRAM_BOT_TOKEN یا GEMINI_API_KEY تنظیم نشده‌اند!")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    # حذف وب‌هوک‌های قبلی برای جلوگیری از تداخل و ارور
    await app.bot.delete_webhook(drop_pending_updates=True)
    
    print("ربات با موفقیت روشن شد و آماده پاسخگویی است...")
    
    async with app:
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())

import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from google import genai

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")

# ساخت کلاینت جدید گوگل جمینی
client = genai.Client(api_key=GEMINI_KEY)

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
    try:
        # استفاده از مدل رسمی و پیش‌فرض کلاینت جدید
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_text,
            config={
                "system_instruction": SYSTEM_PROMPT,
                "temperature": 0.7,
            }
        )
        reply = response.text
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text(f"خطا در دریافت پاسخ: {str(e)}")

def main():
    port = int(os.environ.get("PORT", 8080))
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    if RENDER_EXTERNAL_URL:
        print(f"Starting bot on port {port} via Webhook...")
        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=BOT_TOKEN,
            webhook_url=f"{RENDER_EXTERNAL_URL}/{BOT_TOKEN}",
            drop_pending_updates=True
        )
    else:
        print("Starting bot via Polling...")
        app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

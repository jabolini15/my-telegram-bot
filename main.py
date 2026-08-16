import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")

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
            {
                "parts": [{"text": user_text}]
            }
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
            error_msg = data.get("error", {}).get("message", "خطای ناشناخته")
            await update.message.reply_text(f"خطا در API جمینی: {error_msg}")
            
    except Exception as e:
        await update.message.reply_text(f"خطا در ارتباط: {str(e)}")

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

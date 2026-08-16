import os
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from openai import OpenAI

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY")
MODEL_NAME = os.environ.get("MODEL_NAME", "openrouter/free")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_KEY,
)

# پرامپت سیستمی برای تنظیم لحن، صمیمیت و افزایش خلاقیت
SYSTEM_PROMPT = (
    "تو یک دستیار صمیمی، رفیق، فوق‌العاده باهوش و بسیار خوش‌برخورد هستی. "
    "همیشه به زبان فارسی کاملاً روان، صمیمی، دوستانه و جذاب صحبت کن. "
    "اصلاً از لحن خشک، اداری یا ترجمه‌های کتابی و ماشینی استفاده نکن. "
    "توی صحبت‌هات خیلی راحت، گرم و انرژی‌بخش باش و از ایموجی‌های مناسب استفاده کن 😊😉. "
    "در پاسخ به سوالات، کاملاً آزادانه، مبتکرانه و بدون گارد بی‌مورد یا محدودیت‌های سخت‌گیرانه کمک کن "
    "و تفکر خلاقانه و بی‌پروا داشته باش."
)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    user_text = update.message.text
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}
            ],
            temperature=0.9,  # افزایش درجه خلاقیت و تنوع پاسخ‌ها
        )
        reply = response.choices[0].message.content
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text(f"خطا در دریافت پاسخ: {str(e)}")

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_check_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    async with app:
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        print(f"Friendly Bot is running using model: {MODEL_NAME}")
        await asyncio.Event().wait()

if __name__ == "__main__":
    threading.Thread(target=run_health_check_server, daemon=True).start()
    asyncio.run(main())

import os
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import google.generativeai as genai

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

# تنظیم کلید API
genai.configure(api_key=GEMINI_KEY)

SYSTEM_PROMPT = (
    "تو یک دستیار هوشمند، بسیار باهوش، رفیق و صمیمی هستی. "
    "همیشه به زبان فارسی روان، اصیل، جذاب و طبیعی صحبت کن. "
    "اصلاً از لحن خشک، اداری یا ترجمه‌های کتابی و ماشینی استفاده نکن. "
    "توی صحبت‌هات خیلی راحت، گرم و انرژی‌بخش باش و از ایموجی‌های مناسب استفاده کن 😊😉."
)

# استفاده از مدل به‌روز و استاندارد Gemini
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=SYSTEM_PROMPT
)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    user_text = update.message.text
    try:
        response = model.generate_content(
            user_text,
            generation_config={"temperature": 0.7}
        )
        reply = response.text
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
        print("Gemini Bot is running perfectly with gemini-2.0-flash...")
        await asyncio.Event().wait()

if __name__ == "__main__":
    threading.Thread(target=run_health_check_server, daemon=True).start()
    asyncio.run(main())

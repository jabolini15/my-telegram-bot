import os
import sys
import threading
import requests
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# ۱. دریافت متغیرهای محیطی
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
PORT = int(os.environ.get("PORT", "10000"))

# ۲. ساخت سرور وب برای تایید Render (جلوگیری از خطای Port Scan Timeout)
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass  # خاموش کردن لاگ‌های اضافی HTTP

def start_http_server():
    try:
        server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
        print(f"--> Web server listening on port {PORT}")
        server.serve_forever()
    except Exception as e:
        print(f"--> Web server error: {e}")

# اجرای سرور وب در همان لحظه اول اجرای برنامه
threading.Thread(target=start_http_server, daemon=True).start()

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
    
    # تست خودکار مدل‌ها در صورت قطعی یا ۴۰۴ یکی از آن‌ها
    models = ["gemini-1.5-flash", "gemini-2.0-flash"]
    reply_text = None

    for model_name in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_KEY}"
        payload = {
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [{"parts": [{"text": user_text}]}],
            "generationConfig": {"temperature": 0.7}
        }
        
        try:
            res = requests.post(url, json=payload, timeout=25)
            data = res.json()
            if res.status_code == 200 and "candidates" in data:
                reply_text = data["candidates"][0]["content"]["parts"][0]["text"]
                break
            else:
                err_msg = data.get("error", {}).get("message", "")
                print(f"Model {model_name} failed: {res.status_code} - {err_msg}")
        except Exception as ex:
            print(f"Request error for {model_name}: {ex}")

    if reply_text:
        await update.message.reply_text(reply_text)
    else:
        await update.message.reply_text("متأسفانه مشکلی در ارتباط با API جمینی وجود دارد. لطفا چند لحظه بعد پیام بده.")

async def main():
    if not BOT_TOKEN or not GEMINI_KEY:
        print("ERROR: TELEGRAM_BOT_TOKEN or GEMINI_API_KEY environment variable is missing!")
        sys.exit(1)

    print("--> Starting Telegram Bot...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    # پاک کردن وب‌هوک‌های قدیمی برای جلوگیری از ارور Conflict
    await app.bot.delete_webhook(drop_pending_updates=True)

    print("--> Bot is live and running!")
    async with app:
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())

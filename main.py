import os
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
PORT = int(os.environ.get("PORT", 10000))

SYSTEM_PROMPT = (
    "تو یک دستیار هوشمند، بسیار باهوش، رفیق و صمیمی هستی. "
    "همیشه به زبان فارسی روان، اصیل، جذاب و طبیعی صحبت کن. "
    "اصلاً از لحن خشک، اداری یا ترجمه‌های کتابی و ماشینی استفاده نکن. "
    "توی صحبت‌هات خیلی راحت، گرم و انرژی‌بخش باش و از ایموجی‌های مناسب استفاده کن 😊😉."
)

def get_response_from_gemini(user_text: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"parts": [{"text": user_text}]}],
        "generationConfig": {"temperature": 0.7}
    }
    try:
        res = requests.post(url, json=payload, timeout=25)
        data = res.json()
        if res.status_code == 200 and "candidates" in data:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        
        err_msg = data.get("error", {}).get("message", "خطای نامشخص")
        return f"⚠️ خطا از سمت گوگل:\n{err_msg}"
    except Exception as e:
        return f"⚠️ خطای شبکه: {e}"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_text = update.message.text
    reply = get_response_from_gemini(user_text)
    await update.message.reply_text(reply)

# سرور ساختگی سبک برای پاسخ به UptimeRobot
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")
    
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_health_check_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthCheckHandler)
    print(f"Health check server running on port {PORT}")
    server.serve_forever()

def main():
    if not BOT_TOKEN or not GEMINI_KEY:
        print("Error: TELEGRAM_BOT_TOKEN or GEMINI_API_KEY is missing!")
        return

    # اجرای سرور Health Check در یک رشته (Thread) جداگانه
    Thread(target=run_health_check_server, daemon=True).start()

    # اجرای ربات تلگرام با روش Polling
    print("Starting Polling...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

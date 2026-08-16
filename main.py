import os
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from groq import Groq

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_KEY = os.environ.get("GROQ_API_KEY")

groq_client = Groq(api_key=GROQ_KEY)

SYSTEM_PROMPT = (
    "تو یک دستیار هوشمند، بسیار باهوش، خوش‌برخورد و مسلط به زبان فارسی هستی. "
    "پاسخ‌هایت باید کاملاً روان، واضح، منطقی، بدون ترجمه تحت‌اللفظی و با لحنی دوستانه و محترمانه باشند. "
    "از به کار بردن جملات نامفهوم یا گنگ خودداری کن و موضوعات را شفاف و شیوا توضیح بده."
)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    user_text = update.message.text
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
        )
        reply = chat_completion.choices[0].message.content
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
        print("Bot is running with enhanced system prompt...")
        await asyncio.Event().wait()

if __name__ == "__main__":
    threading.Thread(target=run_health_check_server, daemon=True).start()
    asyncio.run(main())

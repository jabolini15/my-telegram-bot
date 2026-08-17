import os
import base64
import asyncio
import aiohttp
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
PORT = int(os.environ.get("PORT", 10000))

# پرامپت جدید برای صراحت کامل، عدم سانسور رفتاری و رک بودن
SYSTEM_PROMPT = (
    "تو یک دستیار کاملاً آزاد، بی‌پرده، صریح، رک و رفیق شفیق هستی. "
    "اصلاً احتیاط بی‌مورد نکن، نصیحت نکن، و ادای ناظران اخلاقی را درنیاور. "
    "خیلی رک، بدون سانسور رفتاری، بی‌پردگی کامل و مستقیم حرفت را بزن. "
    "از زبان فارسی عامیانه، طبیعی، باحال، رفیقانه و بدون رسمی‌بازی استفاده کن 😊😉."
)

user_chat_history = {}

MODELS_TO_TRY = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash"
]

# خاموش کردن کامل فیلترهای محتوایی و ایمنی گوگل
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
]

async def get_response_from_gemini(user_id: int, new_parts: list) -> str:
    if user_id not in user_chat_history:
        user_chat_history[user_id] = []

    user_chat_history[user_id].append({"role": "user", "parts": new_parts})

    if len(user_chat_history[user_id]) > 10:
        user_chat_history[user_id] = user_chat_history[user_id][-10:]

    last_error = ""
    async with aiohttp.ClientSession() as session:
        for model_name in MODELS_TO_TRY:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_KEY}"
            payload = {
                "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "contents": user_chat_history[user_id],
                "safetySettings": SAFETY_SETTINGS,  # اعمال عدم محدودیت
                "generationConfig": {
                    "temperature": 0.9, # افزایش خلاقیت و صراحت در پاسخ
                    "maxOutputTokens": 4096
                }
            }
            try:
                async with session.post(url, json=payload, timeout=35) as res:
                    data = await res.json()
                    if res.status == 200 and "candidates" in data:
                        bot_reply = data["candidates"][0]["content"]["parts"][0]["text"]
                        
                        user_chat_history[user_id].append({
                            "role": "model",
                            "parts": [{"text": bot_reply}]
                        })
                        return bot_reply
                    
                    err_msg = data.get("error", {}).get("message", f"Status {res.status}")
                    last_error = f"{model_name}: {err_msg}"
            except Exception as e:
                last_error = f"{model_name}: {e}"

    return f"⚠️ خطا در دریافت پاسخ از گوگل:\n{last_error}"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user_id = update.message.from_user.id
    user_text = update.message.text or update.message.caption or "این تصویر را تحلیل کن."
    parts = []

    if update.message.photo:
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        base64_image = base64.b64encode(photo_bytes).decode('utf-8')
        
        parts.append({
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": base64_image
            }
        })

    parts.append({"text": user_text})

    await update.message.chat.send_action("typing")

    reply = await get_response_from_gemini(user_id, parts)
    await update.message.reply_text(reply)

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
    server.serve_forever()

def main():
    if not BOT_TOKEN or not GEMINI_KEY:
        print("Error: TELEGRAM_BOT_TOKEN or GEMINI_API_KEY is missing!")
        return

    Thread(target=run_health_check_server, daemon=True).start()

    print("Starting Polling with Unfiltered Prompt & Safety Settings...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler((filters.TEXT | filters.PHOTO) & (~filters.COMMAND), handle_message))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

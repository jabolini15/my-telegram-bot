import os
import requests
import asyncio
from aiohttp import web
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")
PORT = int(os.environ.get("PORT", 10000))

SYSTEM_PROMPT = (
    "تو یک دستیار هوشمند، بسیار باهوش، رفیق و صمیمی هستی. "
    "همیشه به زبان فارسی روان، اصیل، جذاب و طبیعی صحبت کن. "
    "اصلاً از لحن خشک، اداری یا ترجمه‌های کتابی و ماشینی استفاده نکن. "
    "توی صحبت‌هات خیلی راحت، گرم و انرژی‌بخش باش و از ایموجی‌های مناسب استفاده کن 😊😉."
)

ACTIVE_MODELS = [
    "gemini-1.5-flash",
    "gemini-1.5-pro"
]

def get_response_from_gemini(user_text: str) -> str:
    for model_name in ACTIVE_MODELS:
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
                return data["candidates"][0]["content"]["parts"][0]["text"]
            
            print(f"Model {model_name} returned status {res.status_code}: {data.get('error', {}).get('message')}")
        except Exception as e:
            print(f"Error requesting {model_name}: {e}")

    return "⚠️ متأسفانه در حال حاضر پاسخی دریافت نشد. لطفاً API Key خود را بررسی کنید."

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_text = update.message.text
    reply = get_response_from_gemini(user_text)
    await update.message.reply_text(reply)

# هندر پاسخ برای UptimeRobot روی آدرس اصلی
async def handle_ping(request):
    return web.Response(text="OK", status=200)

async def main():
    if not BOT_TOKEN or not GEMINI_KEY:
        print("Error: TELEGRAM_BOT_TOKEN or GEMINI_API_KEY is missing!")
        return

    # ساخت اپلیکیشن تلگرام
    ptb_app = ApplicationBuilder().token(BOT_TOKEN).build()
    ptb_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    await ptb_app.initialize()
    await ptb_app.start()

    # ساخت وب‌سرور aiohttp برای پشتیبانی از وب‌هوک و UptimeRobot
    web_app = web.Application()
    web_app.router.add_get("/", handle_ping)
    web_app.router.add_head("/", handle_ping)

    if RENDER_EXTERNAL_URL:
        webhook_url = f"{RENDER_EXTERNAL_URL}/{BOT_TOKEN}"
        await ptb_app.bot.set_webhook(url=webhook_url, drop_pending_updates=True)

        async def telegram_webhook(request):
            data = await request.json()
            update = Update.de_json(data, ptb_app.bot)
            await ptb_app.process_update(update)
            return web.Response(text="OK")

        web_app.router.add_post(f"/{BOT_TOKEN}", telegram_webhook)
        
        runner = web.AppRunner(web_app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", PORT)
        await site.start()
        print(f"Web server & Webhook live on port {PORT}")
        await asyncio.Event().wait()
    else:
        await ptb_app.updater.start_polling(drop_pending_updates=True)

if __name__ == "__main__":
    asyncio.run(main())

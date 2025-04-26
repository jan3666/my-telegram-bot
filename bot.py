import sqlite3
import datetime
import logging
import requests
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# قراءة التوكن من المتغير البيئي
TOKEN = os.getenv('7619276075:AAEYYo5PCxL4rUUb1x7prU3JYodOt6Jmr5o')  # قم بتخزين التوكن في متغير بيئي بإسم 'BOT_TOKEN'

# إعداد اللوجينغ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# إعداد قاعدة البيانات
conn = sqlite3.connect('subs.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, payment_method TEXT, paid_until DATE)''')
conn.commit()

# قراءة URL الـ API من المتغير البيئي
API_URL = os.getenv('https://github.com/jan3666/my-telegram-bot.git')  # قم بتخزين الـ API URL في متغير بيئي بإسم 'API_URL'

# أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💳 ادفع الآن", url="https://paypal.me/jandavid366?country.x=DE&locale.x=de_DE")],
        [InlineKeyboardButton("💰 الدفع عبر USDT (TRC20)", url="https://link.trustwallet.com/send?coin=195&address=TFkZd74WFiK16V8tovM1cyJSv45aTLpHHS&token_id=TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 أهلاً بك، لاشتراك شهري اضغط على إحدى الطرق التالية للدفع:\n\n"
        "1. 💳 الدفع الإلكتروني.\n"
        "2. 💰 الدفع عبر USDT (شبكة TRC20).\n\n"
        "📩 بعد الدفع، أرسل بياناتك بالطريقة التالية:\n\n"
        "`telegram_id,username,method`\n\n"
        "📌 مثال: `12345678,username,usdt`",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# أمر /subscribe
async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💳 تم تفعيل الاشتراك بنجاح.")

# استقبال بيانات الدفع كرسالة نصية
async def payment_success(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = update.message.text.split(",")  # "telegram_id,username,method"
        user_id = int(data[0])
        username = data[1]
        method = data[2]
        paid_until = (datetime.datetime.now() + datetime.timedelta(days=30)).date()

        # تخزين البيانات في قاعدة البيانات
        c.execute("REPLACE INTO users (id, username, payment_method, paid_until) VALUES (?, ?, ?, ?)",
                  (user_id, username, method, paid_until))
        conn.commit()

        await context.bot.send_message(chat_id=user_id, text=f"✅ تم تفعيل اشتراكك بنجاح حتى {paid_until}")

        # إرسال البيانات إلى السيرفر الخارجي
        response = requests.post(API_URL, json={'user_id': user_id, 'username': username, 'method': method, 'paid_until': str(paid_until)})

        if response.status_code == 200:
            await update.message.reply_text("✅ تم إرسال البيانات إلى السيرفر بنجاح.")
        else:
            await update.message.reply_text("❌ فشل إرسال البيانات إلى السيرفر. حاول مرة أخرى.")

    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ أثناء معالجة الدفع: {e}")

        # إرسال البيانات إلى السيرفر الخارجي
        response = requests.post(API_URL, json={'user_id': user_id, 'username': username, 'method': method, 'paid_until': str(paid_until)})

# إعداد الـ Application
async def main():
    application = Application.builder().token(TOKEN).build()

    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, payment_success))

    # بدء البوت
    await application.run_polling()

# إذا كان هذا الملف يتم تشغيله مباشرة
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

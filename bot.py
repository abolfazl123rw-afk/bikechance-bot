import logging
import sqlite3
import random
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

TOKEN = "8976579778:AAEzTMKr34TbVKM87vRdURJSzDusVT43UrA"
ADMIN_ID = 8134673501
CARD_NUMBER = "6037-7012-0879-3270"
CARD_OWNER = "ابوالفضل کاظم شعار"
PRICE = "۵۰,۰۰۰ تومان"
CAPACITY = 2000

logging.basicConfig(level=logging.INFO)

def init_db():
    conn = sqlite3.connect("bikechance.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        name TEXT, city TEXT, phone TEXT,
        tracking TEXT, paid INTEGER DEFAULT 0,
        approved INTEGER DEFAULT 0, rejected INTEGER DEFAULT 0,
        date TEXT
    )""")
    conn.commit()
    conn.close()

def db_exec(query, params=()):
    conn = sqlite3.connect("bikechance.db")
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    result = c.fetchall()
    conn.close()
    return result

def count_users(approved_only=False):
    if approved_only:
        return db_exec("SELECT COUNT(*) FROM users WHERE approved=1")[0][0]
    return db_exec("SELECT COUNT(*) FROM users")[0][0]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = count_users()
    keyboard = [["📝 ثبت‌نام در قرعه‌کشی"], ["ℹ️ راهنما", "📊 ظرفیت"]]
    await update.message.reply_text(
        "سلام! به سامانه رسمی قرعه‌کشی دوچرخه خوش آمدی 🚲\n\n"
        f"👥 تا الان {total} نفر از {CAPACITY} نفر ثبت‌نام کردن.\n\n"
        "برای شرکت، دکمه ثبت‌نام رو بزن.",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 راهنما:\n\n"
        "1️⃣ ثبت‌نام کن\n"
        f"2️⃣ {PRICE} واریز کن\n"
        "3️⃣ عکس رسید بفرست\n"
        "4️⃣ منتظر تأیید بمون\n"
        "5️⃣ با /status وضعیتت رو چک کن\n\n"
        "⚠️ توجه: هر رسید جعلی، منجر به حذف میشه."
    )

async def capacity_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = count_users()
    approved = count_users(approved_only=True)
    remaining = CAPACITY - approved
    await update.message.reply_text(
        f"📊 ظرفیت قرعه‌کشی:\n\n"
        f"👥 ثبت‌نام‌شده: {total} نفر\n"
        f"✅ تأییدشده: {approved} نفر\n"
        f"🎯 باقی‌مونده: {remaining} نفر\n"
        f"📈 درصد پر شدن: {int(approved/CAPACITY*100)}%"
    )

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    total = count_users()
    approved = db_exec("SELECT COUNT(*) FROM users WHERE approved=1")[0][0]
    pending = db_exec("SELECT COUNT(*) FROM users WHERE paid=1 AND approved=0 AND rejected=0")[0][0]
    rejected = db_exec("SELECT COUNT(*) FROM users WHERE rejected=1")[0][0]
    await update.message.reply_text(
        f"📊 آمار کامل:\n\n"
        f"👥 کل ثبت‌نام: {total}\n"
        f"✅ تأییدشده: {approved}\n"
        f"⏳ در انتظار: {pending}\n"
        f"❌ رد شده: {rejected}\n"
        f"💰 پول جمع‌شده (تأییدشده): {approved * 50000:,} تومان\n"
        f"🎯 ظرفیت: {approved}/{CAPACITY}"
    )

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    result = db_exec("SELECT name, city, phone, tracking, paid, approved, rejected FROM users WHERE user_id=?", (user_id,))
    if not result:
        await update.message.reply_text("❌ شما هنوز ثبت‌نام نکردی. /start رو بزن.")
        return
    name, city, phone, tracking, paid, approved, rejected = result[0]
    if approved:
        status = "✅ تأییدشده - در قرعه‌کشی شرکت دادی"
    elif rejected:
        status = "❌ رد شده (رسید نامعتبر)"
    elif paid:
        status = "⏳ در انتظار تأیید ادمین"
    else:
        status = "💳 در انتظار پرداخت"
    await update.message.reply_text(
        f"📋 وضعیت شما:\n\n"
        f"👤 نام: {name}\n"
        f"🏙 شهر: {city}\n"
        f"📞 تلفن: {phone}\n"
        f"🎫 کد پیگیری: {tracking}\n"
        f"📌 وضعیت: {status}"
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id
    existing = db_exec("SELECT user_id FROM users WHERE user_id=?", (user_id,))

    if text == "📝 ثبت‌نام در قرعه‌کشی":
        if existing:
            await update.message.reply_text("شما قبلاً ثبت‌نام کردی! با /status وضعیتت رو ببین.")
            return
        context.user_data["step"] = "GET_NAME"
        await update.message.reply_text("لطفاً نام و نام خانوادگی خودت رو بنویس:")
    elif text == "ℹ️ راهنما":
        await help_cmd(update, context)
    elif text == "📊 ظرفیت":
        await capacity_cmd(update, context)
    elif context.user_data.get("step") == "GET_NAME":
        context.user_data["name"] = text
        context.user_data["step"] = "GET_CITY"
        await update.message.reply_text("کدوم شهری؟")
    elif context.user_data.get("step") == "GET_CITY":
        context.user_data["city"] = text
        context.user_data["step"] = "GET_PHONE"
        await update.message.reply_text("شماره تلفنت رو بنویس:")
    elif context.user_data.get("step") == "GET_PHONE":
        phone = text
        name = context.user_data.get("name", "")
        city = context.user_data.get("city", "")
        tracking = str(random.randint(100000, 999999))
        db_exec(
            "INSERT INTO users (user_id, name, city, phone, tracking, date) VALUES (?,?,?,?,?,?)",
            (user_id, name, city, phone, tracking, datetime.now().strftime("%Y/%m/%d %H:%M"))
        )
        context.user_data["step"] = None
        await update.message.reply_text(
            f"ممنون {name} عزیز! ✅\n\n"
            f"برای تکمیل، مبلغ {PRICE} رو واریز کن:\n\n"
            f"💳 {CARD_NUMBER}\n"
            f"به نام: {CARD_OWNER}\n\n"
            f"🎫 کد پیگیری شما: {tracking}\n"
            "بعد از واریز، عکس رسید رو بفرست."
        )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    result = db_exec("SELECT name, city, phone, tracking, approved FROM users WHERE user_id=?", (user_id,))
    if not result:
        await update.message.reply_text("اول /start رو بزن و ثبت‌نام کن.")
        return
    name, city, phone, tracking, approved = result[0]
    if approved:
        await update.message.reply_text("✅ شما قبلاً تأیید شدی.")
        return
    db_exec("UPDATE users SET paid=1 WHERE user_id=?", (user_id,))
    await update.message.reply_text(
        f"✅ رسید دریافت شد!\n\n"
        f"🎫 کد پیگیری: {tracking}\n"
        "منتظر تأیید ادمین باش. با /status وضعیتت رو چک کن."
    )
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ تأیید", callback_data=f"approve_{user_id}"),
        InlineKeyboardButton("❌ رد", callback_data=f"reject_{user_id}")
    ]])
    await context.bot.send_photo(
        ADMIN_ID,
        photo=update.message.photo[-1].file_id,
        caption=(
            f"💰 رسید جدید!\n\n"
            f"👤 نام: {name}\n"
            f"🏙 شهر: {city}\n"
            f"📞 تلفن: {phone}\n"
            f"🎫 کد پیگیری: {tracking}\n"
            f"🆔 آیدی: {user_id}"
        ),
        reply_markup=keyboard
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return
    action, uid = query.data.split("_")
    uid = int(uid)
    result = db_exec("SELECT name FROM users WHERE user_id=?", (uid,))
    if not result:
        return
    name = result[0][0]
    if action == "approve":
        db_exec("UPDATE users SET approved=1, rejected=0 WHERE user_id=?", (uid,))
        await query.edit_message_caption(caption=f"✅ تأیید شد: {name}")
        try:
            await context.bot.send_message(uid, "🎉 رسید شما تأیید شد! در قرعه‌کشی شرکت داده شدی.")
        except:
            pass
    else:
        db_exec("UPDATE users SET approved=0, rejected=1 WHERE user_id=?", (uid,))
        await query.edit_message_caption(caption=f"❌ رد شد: {name}")
        try:
            await context.bot.send_message(uid, "❌ متأسفانه رسید شما تأیید نشد. با پشتیبانی تماس بگیر.")
        except:
            pass

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("capacity", capacity_cmd))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("ربات روشن شد...")
    app.run_polling()

if __name__ == "__main__":
    main()

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
SUPPORT_USERNAME = "@Abolfazl475386"
CHANNEL_USERNAME = "@BikeChanceOfficial"

PRIZE_1 = "۳۰ میلیون تومان"
PRIZE_2 = "۱۵ میلیون تومان"
PRIZE_3 = "۵ میلیون تومان"

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
    c.execute("""CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
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

def get_setting(key, default=""):
    r = db_exec("SELECT value FROM settings WHERE key=?", (key,))
    return r[0][0] if r else default

def set_setting(key, value):
    db_exec("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))

def count_users(approved_only=False):
    if approved_only:
        return db_exec("SELECT COUNT(*) FROM users WHERE approved=1")[0][0]
    return db_exec("SELECT COUNT(*) FROM users")[0][0]

def capacity_bar(approved):
    filled = int(approved / CAPACITY * 20)
    return "█" * filled + "░" * (20 - filled)

async def check_membership(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    is_member = await check_membership(user_id, context)

    if not is_member:
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}")
        ], [
            InlineKeyboardButton("✅ عضو شدم", callback_data="check_join")
        ]])
        await update.message.reply_text(
            "⚠️ برای استفاده از بات، اول باید عضو کانال رسمی بشی:\n\n"
            f"📢 {CHANNEL_USERNAME}\n\n"
            "بعد از عضویت، دکمه «عضو شدم» رو بزن.",
            reply_markup=keyboard
        )
        return

    total = count_users()
    approved = count_users(approved_only=True)
    remaining = CAPACITY - approved
    bar = capacity_bar(approved)
    youtube = get_setting("youtube_live", "")

    prize_text = (
        "🏆 جوایز:\n"
        f"🥇 {PRIZE_1}\n"
        f"🥈 {PRIZE_2}\n"
        f"🥉 {PRIZE_3}\n"
    )

    if approved >= CAPACITY:
        msg = (
            "🔔 ظرفیت تکمیل شد!\n\n"
            f"👥 {approved} نفر شرکت کردن\n"
            "🏆 قرعه‌کشی به زودی در یوتیوب زنده پخش میشه.\n\n"
            f"{prize_text}\n"
        )
        if youtube:
            msg += f"📺 لینک لایو: {youtube}\n"
        msg += f"\n📞 پشتیبانی: {SUPPORT_USERNAME}"
    else:
        msg = (
            "سلام! به سامانه رسمی قرعه‌کشی دوچرخه خوش آمدی 🚲\n\n"
            f"{prize_text}\n"
            f"📊 ظرفیت:\n[{bar}]\n"
            f"✅ تأییدشده: {approved} نفر\n"
            f"🎯 باقی‌مونده: {remaining} نفر\n\n"
            "🏁 قرعه‌کشی به محض تکمیل ۲۰۰۰ نفر برگزار میشه.\n"
            "📺 لایو زنده از یوتیوب\n\n"
            "برای شرکت، دکمه ثبت‌نام رو بزن.\n\n"
            f"📞 پشتیبانی: {SUPPORT_USERNAME}"
        )

    keyboard = [["📝 ثبت‌نام در قرعه‌کشی"], ["ℹ️ راهنما", "📊 ظرفیت", "🎁 جوایز"]]
    await update.message.reply_text(
        msg,
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    is_member = await check_membership(user_id, context)
    if is_member:
        await query.message.delete()
        await query.message.reply_text(
            "✅ عضویت تأیید شد!\n\n"
            "حالا /start رو بزن تا شروع کنیم."
        )
    else:
        await query.answer("❌ هنوز عضو نشدی!", show_alert=True)

async def prizes_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎁 جوایز قرعه‌کشی:\n\n"
        f"🥇 نفر اول: {PRIZE_1}\n"
        f"🥈 نفر دوم: {PRIZE_2}\n"
        f"🥉 نفر سوم: {PRIZE_3}\n\n"
        f"💳 ورودی: {PRICE}\n"
        f"👥 ظرفیت: {CAPACITY} نفر\n\n"
        "🏁 قرعه‌کشی به محض تکمیل ظرفیت، زنده در یوتیوب برگزار میشه.\n\n"
        f"📞 پشتیبانی: {SUPPORT_USERNAME}"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    youtube = get_setting("youtube_live", "")
    msg = (
        "📌 راهنما:\n\n"
        "1️⃣ ثبت‌نام کن\n"
        f"2️⃣ {PRICE} واریز کن\n"
        "3️⃣ عکس رسید بفرست\n"
        "4️⃣ منتظر تأیید بمون\n"
        "5️⃣ با /status وضعیتت رو چک کن\n\n"
        "🏁 قرعه‌کشی: به محض تکمیل ۲۰۰۰ نفر\n"
        "📺 پخش زنده از یوتیوب\n\n"
        "⚠️ هر رسید جعلی، منجر به حذف میشه.\n"
    )
    if youtube:
        msg += f"\n📺 لایو: {youtube}\n"
    msg += f"\n📞 پشتیبانی: {SUPPORT_USERNAME}"
    await update.message.reply_text(msg)

async def capacity_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = count_users()
    approved = count_users(approved_only=True)
    remaining = CAPACITY - approved
    bar = capacity_bar(approved)
    msg = (
        f"📊 وضعیت ظرفیت:\n\n"
        f"[{bar}]\n\n"
        f"✅ تأییدشده: {approved} نفر\n"
        f"👥 ثبت‌نام‌شده: {total} نفر\n"
        f"🎯 باقی‌مونده: {remaining} نفر\n"
        f"📈 درصد: {int(approved/CAPACITY*100)}%\n\n"
        f"🏁 قرعه‌کشی: به محض تکمیل ۲۰۰۰ نفر"
    )
    youtube = get_setting("youtube_live", "")
    if youtube:
        msg += f"\n📺 لینک لایو: {youtube}"
    await update.message.reply_text(msg)

async def setlive_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text(
            "📺 ست کردن لینک لایو:\n\n"
            "/setlive https://youtube.com/live/xxxxx\n\n"
            "حذف:\n/setlive remove"
        )
        return
    link = " ".join(context.args)
    if link.lower() == "remove":
        set_setting("youtube_live", "")
        await update.message.reply_text("✅ لینک حذف شد.")
    else:
        set_setting("youtube_live", link)
        await update.message.reply_text(f"✅ لینک ست شد:\n{link}")

async def announce_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("مثال:\n/announce پیام شما")
        return
    text = " ".join(context.args)
    users = db_exec("SELECT user_id FROM users WHERE approved=1")
    sent = 0
    for u in users:
        try:
            await context.bot.send_message(u[0], f"📢 اعلان:\n\n{text}")
            sent += 1
        except:
            pass
    await update.message.reply_text(f"✅ پیام به {sent} نفر ارسال شد.")

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    total = count_users()
    approved = count_users(approved_only=True)
    pending = db_exec("SELECT COUNT(*) FROM users WHERE paid=1 AND approved=0 AND rejected=0")[0][0]
    rejected = db_exec("SELECT COUNT(*) FROM users WHERE rejected=1")[0][0]
    youtube = get_setting("youtube_live", "❌ ست نشده")
    await update.message.reply_text(
        f"📊 آمار کامل:\n\n"
        f"👥 کل ثبت‌نام: {total}\n"
        f"✅ تأییدشده: {approved}\n"
        f"⏳ در انتظار: {pending}\n"
        f"❌ رد شده: {rejected}\n"
        f"💰 پول جمع‌شده: {approved * 50000:,} تومان\n"
        f"🎯 ظرفیت: {approved}/{CAPACITY}\n"
        f"📈 درصد: {int(approved/CAPACITY*100)}%\n\n"
        f"📺 لایو: {youtube}\n\n"
        f"دستورات:\n"
        f"/setlive [لینک]\n"
        f"/announce [پیام]"
    )

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    result = db_exec("SELECT name, city, phone, tracking, paid, approved, rejected FROM users WHERE user_id=?", (user_id,))
    if not result:
        await update.message.reply_text("❌ هنوز ثبت‌نام نکردی. /start رو بزن.")
        return
    name, city, phone, tracking, paid, approved, rejected = result[0]
    if approved:
        status = "✅ تأییدشده"
    elif rejected:
        status = "❌ رد شده"
    elif paid:
        status = "⏳ در انتظار تأیید"
    else:
        status = "💳 در انتظار پرداخت"
    approved_now = count_users(approved_only=True)
    await update.message.reply_text(
        f"📋 وضعیت شما:\n\n"
        f"👤 {name}\n"
        f"🏙 {city}\n"
        f"📞 {phone}\n"
        f"🎫 کد پیگیری: {tracking}\n"
        f"📌 وضعیت: {status}\n\n"
        f"🎯 ظرفیت: {approved_now}/{CAPACITY}\n\n"
        f"📞 پشتیبانی: {SUPPORT_USERNAME}"
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id
    existing = db_exec("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    approved_count = count_users(approved_only=True)

    if text == "📝 ثبت‌نام در قرعه‌کشی":
        if existing:
            await update.message.reply_text("قبلاً ثبت‌نام کردی! /status رو بزن.")
            return
        if approved_count >= CAPACITY:
            await update.message.reply_text("❌ ظرفیت تکمیل شده!")
            return
        context.user_data["step"] = "GET_NAME"
        remaining = CAPACITY - approved_count
        await update.message.reply_text(f"👥 ظرفیت باقی‌مونده: {remaining} نفر\n\nنام و نام خانوادگی:")
    elif text == "ℹ️ راهنما":
        await help_cmd(update, context)
    elif text == "📊 ظرفیت":
        await capacity_cmd(update, context)
    elif text == "🎁 جوایز":
        await prizes_cmd(update, context)
    elif context.user_data.get("step") == "GET_NAME":
        context.user_data["name"] = text
        context.user_data["step"] = "GET_CITY"
        await update.message.reply_text("کدوم شهری؟")
    elif context.user_data.get("step") == "GET_CITY":
        context.user_data["city"] = text
        context.user_data["step"] = "GET_PHONE"
        await update.message.reply_text("شماره تلفنت:")
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
        approved_now = count_users(approved_only=True)
        remaining_now = CAPACITY - approved_now
        await update.message.reply_text(
            f"ممنون {name} عزیز! ✅\n\n"
            f"مبلغ {PRICE} رو واریز کن:\n\n"
            f"💳 {CARD_NUMBER}\n"
            f"به نام: {CARD_OWNER}\n\n"
            f"🎫 کد پیگیری شما: {tracking}\n"
            f"👥 ظرفیت باقی‌مونده: {remaining_now} نفر\n\n"
            "⚠️ موقع واریز، حتماً این کد رو تو توضیحات تراکنش بنویس.\n\n"
            "بعد از واریز، عکس رسید رو بفرست.\n\n"
            f"📞 پشتیبانی: {SUPPORT_USERNAME}"
        )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    result = db_exec("SELECT name, city, phone, tracking, approved FROM users WHERE user_id=?", (user_id,))
    if not result:
        await update.message.reply_text("اول /start رو بزن.")
        return
    name, city, phone, tracking, approved = result[0]
    if approved:
        await update.message.reply_text("✅ قبلاً تأیید شدی.")
        return
    db_exec("UPDATE users SET paid=1 WHERE user_id=?", (user_id,))
    await update.message.reply_text(
        f"✅ رسید دریافت شد!\n\n"
        f"🎫 کد پیگیری: {tracking}\n"
        "منتظر تأیید باش. /status رو بزن.\n\n"
        f"📞 پشتیبانی: {SUPPORT_USERNAME}"
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
            f"👤 {name}\n"
            f"🏙 {city}\n"
            f"📞 {phone}\n"
            f"🎫 کد: {tracking}\n"
            f"🆔 {user_id}"
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
        approved_count = count_users(approved_only=True)
        if approved_count >= CAPACITY:
            await query.edit_message_caption(caption=f"⚠️ ظرفیت تکمیل شده!\n\n{name}")
            return
        db_exec("UPDATE users SET approved=1, rejected=0 WHERE user_id=?", (uid,))
        new_count = count_users(approved_only=True)
        await query.edit_message_caption(
            caption=f"✅ تأیید شد: {name}\n👥 ظرفیت: {new_count}/{CAPACITY}"
        )
        youtube = get_setting("youtube_live", "")
        msg = (
            f"🎉 رسید شما تأیید شد!\n\n"
            f"👥 ظرفیت: {new_count}/{CAPACITY}\n"
            f"🎯 باقی‌مونده: {CAPACITY - new_count} نفر\n\n"
            "🏁 به محض تکمیل ۲۰۰۰ نفر، قرعه‌کشی زنده در یوتیوب برگزار میشه.\n\n"
            "موفق باشی! 🚲\n"
        )
        if youtube:
            msg += f"\n📺 لایو: {youtube}"
        try:
            await context.bot.send_message(uid, msg)
        except:
            pass

        if new_count >= CAPACITY:
            youtube = get_setting("youtube_live", "")
            all_users = db_exec("SELECT user_id FROM users WHERE approved=1")
            announce_msg = (
                f"🔔 ظرفیت {CAPACITY} نفر تکمیل شد!\n\n"
                f"🏆 قرعه‌کشی به زودی زنده در یوتیوب پخش میشه.\n"
                "📺 منتظر لینک باش.\n"
            )
            if youtube:
                announce_msg += f"\n📺 {youtube}"
            for u in all_users:
                try:
                    await context.bot.send_message(u[0], announce_msg)
                except:
                    pass
            try:
                await context.bot.send_message(ADMIN_ID, f"🔔 ظرفیت {CAPACITY} نفر تکمیل شد!")
            except:
                pass
    else:
        db_exec("UPDATE users SET approved=0, rejected=1 WHERE user_id=?", (uid,))
        await query.edit_message_caption(caption=f"❌ رد شد: {name}")
        try:
            await context.bot.send_message(
                uid,
                f"❌ رسید تأیید نشد.\n\n📞 پشتیبانی: {SUPPORT_USERNAME}"
            )
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
    app.add_handler(CommandHandler("prizes", prizes_cmd))
    app.add_handler(CommandHandler("setlive", setlive_cmd))
    app.add_handler(CommandHandler("announce", announce_cmd))
    app.add_handler(CallbackQueryHandler(check_join_callback, pattern="^check_join$"))
    app.add_handler(CallbackQueryHandler(button_callback, pattern="^(approve|reject)_"))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("ربات روشن شد...")
    app.run_polling()

if __name__ == "__main__":
    main()

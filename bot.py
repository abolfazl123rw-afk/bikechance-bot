import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8976579778:AAEzTMKr34TbVKM87vRdURJSzDusVT43UrA"
ADMIN_ID = 0
CARD_NUMBER = "6037-7012-0879-3270"
CARD_OWNER = "ابوالفضل کاظم شعار"
PRICE = "۵۰,۰۰۰ تومان"

logging.basicConfig(level=logging.INFO)

users = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["📝 ثبت‌نام در قرعه‌کشی"], ["ℹ️ راهنما"]]
    await update.message.reply_text(
        "سلام! به سامانه رسمی قرعه‌کشی دوچرخه خوش آمدی 🚲\n\n"
        "برای شرکت در قرعه‌کشی، دکمه ثبت‌نام رو بزن.",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 راهنما:\n\n"
        "1️⃣ ثبت‌نام کن\n"
        "2️⃣ ۵۰,۰۰۰ تومان واریز کن\n"
        "3️⃣ عکس رسید بفرست\n"
        "4️⃣ منتظر قرعه‌کشی باش\n\n"
        "برنده‌ها به صورت علنی اعلام می‌شن."
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in users:
        await update.message.reply_text("اول ثبت‌نام کن!")
        return
    users[user_id]["paid"] = True
    await update.message.reply_text(
        "✅ رسید دریافت شد!\n\n"
        "بعد از تأیید، بهت خبر می‌دیم.\n"
        f"کد پیگیری: {str(user_id)[-6:]}"
    )
    if ADMIN_ID:
        await context.bot.send_message(
            ADMIN_ID,
            f"💰 رسید جدید از {users[user_id].get('name', 'ناشناس')}"
        )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id

    if text == "📝 ثبت‌نام در قرعه‌کشی":
        users[user_id] = {}
        await update.message.reply_text("لطفاً نام و نام خانوادگی خودت رو بنویس:")
        users[user_id]["step"] = "GET_NAME"
    elif text == "ℹ️ راهنما":
        await help_cmd(update, context)
    elif user_id in users:
        step = users[user_id].get("step")
        if step == "GET_NAME":
            users[user_id]["name"] = text
            users[user_id]["step"] = "GET_CITY"
            await update.message.reply_text("کدوم شهری؟")
        elif step == "GET_CITY":
            users[user_id]["city"] = text
            users[user_id]["step"] = "GET_PHONE"
            await update.message.reply_text("شماره تلفنت رو بنویس:")
        elif step == "GET_PHONE":
            users[user_id]["phone"] = text
            users[user_id]["step"] = "WAIT_PAYMENT"
            await update.message.reply_text(
                f"ممنون {users[user_id]['name']} عزیز! ✅\n\n"
                f"برای تکمیل ثبت‌نام، مبلغ {PRICE} رو به شماره کارت زیر واریز کن:\n\n"
                f"💳 {CARD_NUMBER}\n"
                f"به نام: {CARD_OWNER}\n\n"
                "بعد از واریز، عکس رسید رو همین‌جا بفرست."
            )

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("ربات روشن شد...")
    app.run_polling()

if __name__ == "__main__":
    main()

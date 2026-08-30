"""
Qassoblik uchun Telegram bot.

Bot mijozdan quyidagi ma'lumotlarni ketma-ket so'raydi:
  1. Ism-familiya
  2. Telefon raqam (tugma orqali yuboriladi)
  3. Go'sht turi
  4. Kerakli miqdor (kg)
  5. Manzil / lokatsiya

Yig'ilgan ma'lumot chiroyli formatda ADMIN GURUH ga xabar sifatida yuboriladi.
"""

import html
import logging
import os

from dotenv import load_dotenv
from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton,
    Update,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")  # masalan: -1001234567890

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Suhbat bosqichlari
NAME, PHONE, MEAT_TYPE, AMOUNT, LOCATION = range(5)

MEAT_TYPES = ["🐄 Mol go'shti", "🐑 Qo'y go'shti", "🐔 Tovuq go'shti", "✍️ Boshqa"]


# ---------- Yordamchi funksiyalar ----------

def esc(value) -> str:
    """Xabar matnidagi maxsus belgilarni (masalan <, >, &, _) xavfsiz qilib qaytaradi,
    shunda mijoz ma'lumotidagi istalgan belgi Telegram formatlashini buzmaydi."""
    return html.escape(str(value)) if value is not None else ""


def order_summary(data: dict) -> str:
    return (
        "🆕 <b>Yangi buyurtma!</b>\n\n"
        f"👤 <b>Ism:</b> {esc(data.get('name'))}\n"
        f"📞 <b>Telefon:</b> {esc(data.get('phone'))}\n"
        f"🥩 <b>Go'sht turi:</b> {esc(data.get('meat_type'))}\n"
        f"⚖️ <b>Miqdor:</b> {esc(data.get('amount'))} kg\n"
        f"📍 <b>Manzil:</b> {esc(data.get('location'))}\n"
        f"🔗 <b>Mijoz:</b> @{esc(data.get('username'))}"
    )


# ---------- Suhbat bosqichlari ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Assalomu alaykum! 👋\n"
        "Qassobxonamizga xush kelibsiz.\n\n"
        "Buyurtma berish uchun /order buyrug'ini yuboring.\n"
        "Bekor qilish uchun istalgan vaqtda /cancel yozing."
    )
    return ConversationHandler.END


async def order_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    context.user_data["username"] = update.effective_user.username or update.effective_user.full_name
    await update.message.reply_text(
        "Ism-familiyangizni kiriting:",
        reply_markup=ReplyKeyboardRemove(),
    )
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text
    contact_button = KeyboardButton("📱 Raqamni yuborish", request_contact=True)
    keyboard = ReplyKeyboardMarkup([[contact_button]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "Telefon raqamingizni tugma orqali yuboring (yoki qo'lda yozing):",
        reply_markup=keyboard,
    )
    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.contact:
        context.user_data["phone"] = update.message.contact.phone_number
    else:
        context.user_data["phone"] = update.message.text

    keyboard = ReplyKeyboardMarkup(
        [[t] for t in MEAT_TYPES], resize_keyboard=True, one_time_keyboard=True
    )
    await update.message.reply_text("Qanday go'sht kerak?", reply_markup=keyboard)
    return MEAT_TYPE


async def get_meat_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["meat_type"] = update.message.text
    await update.message.reply_text(
        "Necha kilogramm kerak? (masalan: 5)",
        reply_markup=ReplyKeyboardRemove(),
    )
    return AMOUNT


async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["amount"] = update.message.text

    location_button = KeyboardButton("📍 Lokatsiyani yuborish", request_location=True)
    keyboard = ReplyKeyboardMarkup([[location_button]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "Yetkazib berish manzilini yuboring (lokatsiya tugmasi orqali) yoki manzilni yozing:",
        reply_markup=keyboard,
    )
    return LOCATION


async def get_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.location:
        lat = update.message.location.latitude
        lon = update.message.location.longitude
        context.user_data["location"] = f"https://maps.google.com/?q={lat},{lon}"
    else:
        context.user_data["location"] = update.message.text

    summary = order_summary(context.user_data)

    # Mijozga tasdiq
    await update.message.reply_text(
        "✅ Buyurtmangiz qabul qilindi! Tez orada siz bilan bog'lanamiz.",
        reply_markup=ReplyKeyboardRemove(),
    )

    # Admin guruhga yuborish
    if GROUP_CHAT_ID:
        await context.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=summary,
            parse_mode="HTML",
        )
    else:
        logger.warning("GROUP_CHAT_ID sozlanmagan — buyurtma faqat logga yozildi: %s", summary)

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "Buyurtma bekor qilindi. Qayta boshlash uchun /order yozing.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN topilmadi. .env faylida BOT_TOKEN ni sozlang.")

    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("order", order_start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler((filters.TEXT | filters.CONTACT) & ~filters.COMMAND, get_phone)],
            MEAT_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_meat_type)],
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_amount)],
            LOCATION: [MessageHandler((filters.TEXT | filters.LOCATION) & ~filters.COMMAND, get_location)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)

    logger.info("Bot ishga tushdi...")
    application.run_polling()


if __name__ == "__main__":
    main()

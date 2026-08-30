"""
Qassoblik uchun Telegram bot.

Asosiy imkoniyatlar:
  - Mijoz birinchi marta yozganda ism va telefonini so'raydi, keyingi safar
    ularni ESLAB QOLADI va qayta so'ramaydi.
  - Mijoz istalgan sondagi mahsulotni (masalan mol go'shti + qo'y go'shti)
    bitta buyurtmaga SAVATCHAGA qo'shib ketishi mumkin.
  - Har bir bosqichda "⬅️ Orqaga" tugmasi bilan fikrini o'zgartirishi mumkin.
  - Mijozning oldingi manzillari eslab qolinadi, keyingi safar ro'yxatdan
    tanlaydi; yangi manzil yuborsa, u ham ro'yxatga qo'shiladi.
  - Yakuniy bosqichda mijoz butun buyurtmani ko'rib, TASDIQLAYDI.

Ma'lumotlar:
  - har bir tasdiqlangan buyurtma ADMIN GURUHGA xabar sifatida yuboriladi
  - (agar SHEET_WEBHOOK_URL sozlangan bo'lsa) Google Sheets'ga ham yoziladi —
    shu jadval orqali mijoz profili keyingi safar o'qib olinadi

Admin guruhda "/hisobot" deb yozilsa, bot bugungi buyurtmalarni bir-biriga
YAQIN turgan mijozlarga guruhlab chiqarib beradi.
"""

import html
import logging
import os
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2

import requests
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
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")
FEEDBACK_GROUP_CHAT_ID = os.getenv("FEEDBACK_GROUP_CHAT_ID")  # taklif/shikoyatlar uchun alohida guruh
SHEET_WEBHOOK_URL = os.getenv("SHEET_WEBHOOK_URL")  # ixtiyoriy, lekin profil/manzil
                                                     # xotirasi ishlashi uchun SHART

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Suhbat bosqichlari
NAME, PHONE, CART_MEAT, CART_AMOUNT, ADDRESS, CONFIRM = range(6)
FEEDBACK_TEXT = 100  # alohida (mustaqil) suhbat uchun holat

# --------------------------------------------------------------------------
# GO'SHT RO'YXATI — shu yerga qo'shish yoki o'chirish orqali ro'yxatni
# o'zgartirasiz. Har bir qator bitta tugma bo'lib chiqadi.
# --------------------------------------------------------------------------
MEAT_TYPES = [
    "🐄 Mol go'shti",
    "🐑 Qo'y go'shti",
    "🐔 Tovuq go'shti",
    "🍖 Jigar / ichki a'zolar",
    "✍️ Boshqa",
]

ORDER_BUTTON_TEXT = "🛒 Buyurtma berish"
FEEDBACK_BUTTON_TEXT = "💬 Fikr-mulohaza / Shikoyat"
MAIN_MENU = ReplyKeyboardMarkup([[ORDER_BUTTON_TEXT], [FEEDBACK_BUTTON_TEXT]], resize_keyboard=True)

BACK_BUTTON = "⬅️ Orqaga"
NEW_ADDRESS_BUTTON = "📍 Yangi manzil yuborish"
CONFIRM_BUTTON = "✅ Tasdiqlash"
CANCEL_BUTTON = "❌ Bekor qilish"

# Yaqin buyurtmalarni bitta guruhga birlashtirish uchun radius (km)
CLUSTER_RADIUS_KM = 1.5


# ---------- Umumiy yordamchi funksiyalar ----------

def esc(value) -> str:
    """Xabar matnidagi maxsus belgilarni xavfsiz qilib qaytaradi."""
    return html.escape(str(value)) if value is not None else ""


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi / 2) ** 2 + cos(p1) * cos(p2) * sin(dlambda / 2) ** 2
    return 2 * r * atan2(sqrt(a), sqrt(1 - a))


def cluster_orders(orders: list) -> tuple:
    located = [o for o in orders if o.get("lat") not in (None, "") and o.get("lon") not in (None, "")]
    unlocated = [o for o in orders if o not in located]

    n = len(located)
    visited = [False] * n
    clusters = []

    for i in range(n):
        if visited[i]:
            continue
        stack = [i]
        visited[i] = True
        group = [located[i]]
        while stack:
            cur = stack.pop()
            for j in range(n):
                if visited[j]:
                    continue
                d = haversine_km(
                    float(located[cur]["lat"]), float(located[cur]["lon"]),
                    float(located[j]["lat"]), float(located[j]["lon"]),
                )
                if d <= CLUSTER_RADIUS_KM:
                    visited[j] = True
                    group.append(located[j])
                    stack.append(j)
        clusters.append(group)

    return clusters, unlocated


# ---------- Google Sheets bilan ishlash (profil, manzillar, buyurtmalar) ----------

def fetch_profile(user_id: int) -> dict | None:
    """Mijozning oldin saqlangan ismi, telefoni va manzillarini o'qiydi.
    Topilmasa yoki Sheets ulanmagan bo'lsa None qaytaradi."""
    if not SHEET_WEBHOOK_URL:
        return None
    try:
        resp = requests.get(
            SHEET_WEBHOOK_URL, params={"action": "profile", "user_id": user_id}, timeout=10
        )
        data = resp.json()
        if not data or not data.get("name") or not data.get("phone"):
            return None
        return {
            "name": data.get("name"),
            "phone": data.get("phone"),
            "addresses": data.get("addresses") or [],
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("Profilni o'qib bo'lmadi: %s", exc)
        return None


def save_profile(user_id: int, name: str, phone: str, addresses: list) -> None:
    if not SHEET_WEBHOOK_URL:
        return
    try:
        requests.post(
            SHEET_WEBHOOK_URL,
            json={
                "action": "save_profile",
                "user_id": user_id,
                "name": name,
                "phone": phone,
                "addresses": addresses,
            },
            timeout=10,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Profilni saqlab bo'lmadi: %s", exc)


def post_order_to_sheet(data: dict) -> None:
    if not SHEET_WEBHOOK_URL:
        return
    addr = data.get("selected_address", {})
    items_str = ", ".join(f"{i['meat_type']} ({i['amount']}kg)" for i in data.get("cart", []))
    payload = {
        "name": data.get("name"),
        "phone": data.get("phone"),
        "items": items_str,
        "address_text": addr.get("address_text") or addr.get("label"),
        "lat": addr.get("lat"),
        "lon": addr.get("lon"),
        "username": data.get("username"),
    }
    try:
        requests.post(SHEET_WEBHOOK_URL, json=payload, timeout=10)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Buyurtmani Sheets'ga yozib bo'lmadi: %s", exc)


# ---------- Klaviatura va matn generatorlari ----------

def build_cart_keyboard(cart: list) -> ReplyKeyboardMarkup:
    rows = [[t] for t in MEAT_TYPES]
    if cart:
        rows.append([f"🧺 Savatni yakunlash ({len(cart)} ta mahsulot)"])
        rows.append([BACK_BUTTON])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def cart_summary_html(cart: list) -> str:
    if not cart:
        return "🧺 Savat hozircha bo'sh."
    lines = ["🧺 <b>Hozirgi savat:</b>"]
    for item in cart:
        lines.append(f"  • {esc(item['meat_type'])} — {esc(item['amount'])} kg")
    return "\n".join(lines)


def build_address_keyboard(addresses: list) -> ReplyKeyboardMarkup:
    rows = [[a["label"]] for a in addresses]
    rows.append([KeyboardButton(NEW_ADDRESS_BUTTON, request_location=True)])
    rows.append([BACK_BUTTON])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def build_confirm_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([[CONFIRM_BUTTON], [BACK_BUTTON, CANCEL_BUTTON]], resize_keyboard=True)


def order_summary_html(data: dict) -> str:
    addr = data.get("selected_address", {})
    lines = [
        "🆕 <b>Yangi buyurtma!</b>\n",
        f"👤 <b>Ism:</b> {esc(data.get('name'))}",
        f"📞 <b>Telefon:</b> {esc(data.get('phone'))}\n",
        "🥩 <b>Mahsulotlar:</b>",
    ]
    for item in data.get("cart", []):
        lines.append(f"  • {esc(item['meat_type'])} — {esc(item['amount'])} kg")
    lines.append(f"\n📍 <b>Manzil:</b> {esc(addr.get('address_text') or addr.get('label'))}")
    lines.append(f"🔗 <b>Mijoz:</b> @{esc(data.get('username'))}")
    return "\n".join(lines)


# ---------- Suhbat bosqichlari ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Assalomu alaykum! 👋\n"
        "Qassobxonamizga xush kelibsiz.\n\n"
        "Buyurtma berish uchun pastdagi tugmani bosing.\n"
        "Bekor qilish uchun istalgan vaqtda /cancel yozing.",
        reply_markup=MAIN_MENU,
    )
    return ConversationHandler.END


async def order_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    user = update.effective_user
    context.user_data["user_id"] = user.id
    context.user_data["username"] = user.username or user.full_name
    context.user_data["cart"] = []

    profile = fetch_profile(user.id)
    if profile:
        context.user_data["name"] = profile["name"]
        context.user_data["phone"] = profile["phone"]
        context.user_data["addresses"] = profile["addresses"]
        await update.message.reply_text(
            f"Xush kelibsiz, {esc(profile['name'])}! 👋\n"
            "Ma'lumotlaringiz eslab qolingan, qayta so'ramayman.\n\n"
            "Qanday mahsulot kerak? Bir nechtasini ham savatga qo'sha olasiz.",
            parse_mode="HTML",
            reply_markup=build_cart_keyboard([]),
        )
        return CART_MEAT

    context.user_data["addresses"] = []
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

    await update.message.reply_text(
        "Rahmat! Endi qanday mahsulot kerakligini tanlang. "
        "Bir nechtasini ham savatga qo'sha olasiz.",
        reply_markup=build_cart_keyboard([]),
    )
    return CART_MEAT


async def cart_meat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    cart = context.user_data.setdefault("cart", [])

    if text == BACK_BUTTON:
        if cart:
            removed = cart.pop()
            await update.message.reply_text(
                f"O'chirildi: {removed['meat_type']} — {removed['amount']} kg\n\n"
                + cart_summary_html(cart),
                parse_mode="HTML",
                reply_markup=build_cart_keyboard(cart),
            )
        return CART_MEAT

    if text.startswith("🧺 Savatni yakunlash"):
        if not cart:
            await update.message.reply_text(
                "Savat hali bo'sh — avval kamida bitta mahsulot tanlang.",
                reply_markup=build_cart_keyboard(cart),
            )
            return CART_MEAT

        addresses = context.user_data.get("addresses", [])
        if addresses:
            msg = "Yetkazib berish manzilini tanlang, yoki yangi manzil yuboring:"
        else:
            msg = "Yetkazib berish manzilini yuboring (📍 tugma orqali — bu eng aniq usul):"
        await update.message.reply_text(msg, reply_markup=build_address_keyboard(addresses))
        return ADDRESS

    if text in MEAT_TYPES:
        context.user_data["current_meat"] = text
        await update.message.reply_text(
            f"{text} — necha kilogramm kerak? (masalan: 5)",
            reply_markup=ReplyKeyboardMarkup([[BACK_BUTTON]], resize_keyboard=True),
        )
        return CART_AMOUNT

    await update.message.reply_text(
        "Iltimos, pastdagi ro'yxatdan tanlang.",
        reply_markup=build_cart_keyboard(cart),
    )
    return CART_MEAT


async def cart_amount_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    cart = context.user_data.setdefault("cart", [])

    if text == BACK_BUTTON:
        context.user_data.pop("current_meat", None)
        await update.message.reply_text(
            "Bekor qilindi. Boshqa mahsulot tanlang:",
            reply_markup=build_cart_keyboard(cart),
        )
        return CART_MEAT

    meat = context.user_data.pop("current_meat", None)
    cart.append({"meat_type": meat, "amount": text})

    await update.message.reply_text(
        f"✅ Savatga qo'shildi: {meat} — {text} kg\n\n" + cart_summary_html(cart),
        parse_mode="HTML",
        reply_markup=build_cart_keyboard(cart),
    )
    return CART_MEAT


async def address_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    addresses = context.user_data.setdefault("addresses", [])

    if update.message.location:
        lat = update.message.location.latitude
        lon = update.message.location.longitude
        new_addr = {
            "label": f"📍 Manzil {len(addresses) + 1}",
            "address_text": f"https://maps.google.com/?q={lat},{lon}",
            "lat": lat,
            "lon": lon,
        }
        addresses.append(new_addr)
        context.user_data["selected_address"] = new_addr
        await update.message.reply_text(
            "Manzil saqlandi ✅ Keyingi safar shu manzilni ro'yxatdan tanlashingiz mumkin bo'ladi.\n\n"
            + order_summary_html(context.user_data),
            parse_mode="HTML",
            reply_markup=build_confirm_keyboard(),
        )
        return CONFIRM

    text = update.message.text

    if text == BACK_BUTTON:
        await update.message.reply_text(
            "Savatga qaytdik:\n\n" + cart_summary_html(context.user_data.get("cart", [])),
            parse_mode="HTML",
            reply_markup=build_cart_keyboard(context.user_data.get("cart", [])),
        )
        return CART_MEAT

    match = next((a for a in addresses if a["label"] == text), None)
    if match:
        context.user_data["selected_address"] = match
    else:
        # Qo'lda yozilgan yangi manzil (koordinatasiz)
        new_addr = {
            "label": f"📍 Manzil {len(addresses) + 1}",
            "address_text": text,
            "lat": None,
            "lon": None,
        }
        addresses.append(new_addr)
        context.user_data["selected_address"] = new_addr

    await update.message.reply_text(
        order_summary_html(context.user_data),
        parse_mode="HTML",
        reply_markup=build_confirm_keyboard(),
    )
    return CONFIRM


async def confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text

    if text == BACK_BUTTON:
        addresses = context.user_data.get("addresses", [])
        await update.message.reply_text(
            "Manzilni qaytadan tanlang:",
            reply_markup=build_address_keyboard(addresses),
        )
        return ADDRESS

    if text == CANCEL_BUTTON:
        context.user_data.clear()
        await update.message.reply_text(
            "Buyurtma bekor qilindi.",
            reply_markup=MAIN_MENU,
        )
        return ConversationHandler.END

    if text != CONFIRM_BUTTON:
        await update.message.reply_text(
            "Iltimos, pastdagi tugmalardan birini tanlang.",
            reply_markup=build_confirm_keyboard(),
        )
        return CONFIRM

    # ---- Tasdiqlandi: yakunlash ----
    summary = order_summary_html(context.user_data)

    await update.message.reply_text(
        "✅ Buyurtmangiz qabul qilindi! Tez orada siz bilan bog'lanamiz.",
        reply_markup=MAIN_MENU,
    )

    if GROUP_CHAT_ID:
        await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=summary, parse_mode="HTML")
    else:
        logger.warning("GROUP_CHAT_ID sozlanmagan — buyurtma faqat logga yozildi: %s", summary)

    post_order_to_sheet(context.user_data)
    save_profile(
        context.user_data.get("user_id"),
        context.user_data.get("name"),
        context.user_data.get("phone"),
        context.user_data.get("addresses", []),
    )

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "Buyurtma bekor qilindi. Qayta boshlash uchun pastdagi tugmani bosing.",
        reply_markup=MAIN_MENU,
    )
    return ConversationHandler.END


# ---------- Admin: kunlik hisobot (yaqin manzillarni guruhlash) ----------

async def hisobot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not SHEET_WEBHOOK_URL:
        await update.message.reply_text(
            "Hisobot uchun Google Sheets ulanmagan. README'dagi \"Google Sheets\" bo'limiga qarang."
        )
        return

    today = datetime.now().strftime("%Y-%m-%d")
    try:
        resp = requests.get(SHEET_WEBHOOK_URL, params={"date": today}, timeout=15)
        rows = resp.json()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Hisobot uchun Sheets'dan o'qib bo'lmadi: %s", exc)
        await update.message.reply_text("Hisobotni olishda xatolik yuz berdi. Birozdan so'ng qayta urinib ko'ring.")
        return

    if not rows:
        await update.message.reply_text(f"{today} uchun hali buyurtma yo'q.")
        return

    orders = []
    for r in rows:
        orders.append({
            "name": r.get("Ism", ""),
            "phone": r.get("Telefon", ""),
            "items": r.get("Mahsulotlar", ""),
            "address": r.get("Manzil matni", ""),
            "lat": r.get("Lat") or None,
            "lon": r.get("Lon") or None,
        })

    clusters, unlocated = cluster_orders(orders)
    clusters.sort(key=len, reverse=True)

    lines = [f"📦 <b>{today} — buyurtmalar (yaqinlik bo'yicha guruhlangan)</b>\n"]
    for idx, group in enumerate(clusters, start=1):
        lines.append(f"\n<b>🗺 {idx}-hudud ({len(group)} ta buyurtma):</b>")
        for o in group:
            lines.append(
                f"  • {esc(o['name'])} — {esc(o['items'])} — {esc(o['phone'])} — "
                f"https://maps.google.com/?q={o['lat']},{o['lon']}"
            )

    if unlocated:
        lines.append(f"\n<b>❓ Aniq lokatsiyasiz ({len(unlocated)} ta):</b>")
        for o in unlocated:
            lines.append(f"  • {esc(o['name'])} — {esc(o['items'])} — {esc(o['phone'])} — {esc(o['address'])}")

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


# ---------- Fikr-mulohaza / Shikoyat (alohida, mustaqil suhbat) ----------

async def feedback_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Fikr, taklif yoki shikoyatingizni yozib qoldiring — biz albatta o'qib chiqamiz. 🙏\n"
        "Bekor qilish uchun /cancel yozing.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return FEEDBACK_TEXT


async def feedback_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    text = update.message.text

    await update.message.reply_text(
        "Rahmat! Fikringiz yetkazildi. 🙏",
        reply_markup=MAIN_MENU,
    )

    if FEEDBACK_GROUP_CHAT_ID:
        lines = [
            "💬 <b>Yangi fikr-mulohaza / shikoyat</b>\n",
            f"👤 <b>Mijoz:</b> {esc(user.full_name)} (@{esc(user.username or '—')})",
        ]
        # Agar bu mijoz avval buyurtma bergan bo'lsa, uning saqlangan ismi/telefonini ham ko'rsatamiz
        profile = fetch_profile(user.id)
        if profile:
            lines.append(f"📞 <b>Telefon (profilidan):</b> {esc(profile.get('phone'))}")
        lines.append(f"\n📝 <b>Matn:</b>\n{esc(text)}")
        await context.bot.send_message(
            chat_id=FEEDBACK_GROUP_CHAT_ID,
            text="\n".join(lines),
            parse_mode="HTML",
        )
    else:
        logger.warning("FEEDBACK_GROUP_CHAT_ID sozlanmagan — fikr faqat logga yozildi: %s", text)

    return ConversationHandler.END


async def feedback_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Bekor qilindi.", reply_markup=MAIN_MENU)
    return ConversationHandler.END


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN topilmadi. .env faylida BOT_TOKEN ni sozlang.")

    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("order", order_start),
            CommandHandler("buyurtma", order_start),
            MessageHandler(filters.Regex(f"^{ORDER_BUTTON_TEXT}$"), order_start),
        ],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler((filters.TEXT | filters.CONTACT) & ~filters.COMMAND, get_phone)],
            CART_MEAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, cart_meat_handler)],
            CART_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, cart_amount_handler)],
            ADDRESS: [MessageHandler((filters.TEXT | filters.LOCATION) & ~filters.COMMAND, address_handler)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    feedback_conv = ConversationHandler(
        entry_points=[
            CommandHandler("feedback", feedback_start),
            CommandHandler("izoh", feedback_start),
            MessageHandler(filters.Regex(f"^{FEEDBACK_BUTTON_TEXT}$"), feedback_start),
        ],
        states={
            FEEDBACK_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, feedback_receive)],
        },
        fallbacks=[CommandHandler("cancel", feedback_cancel)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_handler(feedback_conv)
    application.add_handler(CommandHandler("hisobot", hisobot))

    logger.info("Bot ishga tushdi...")
    application.run_polling()


if __name__ == "__main__":
    main()

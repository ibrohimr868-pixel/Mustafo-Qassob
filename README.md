# Qassoblik Telegram boti

Bu bot mijozlardan buyurtma ma'lumotlarini (ism, telefon, go'sht turi, miqdor, manzil)
yig'adi va sizning admin guruhingizga xabar sifatida yuboradi.

Quyida **nol tajribadan boshlab** botni ishga tushirish bosqichlari yozilgan.

---

## 1-QADAM: Bot yaratish (BotFather)

1. Telegramda **@BotFather** ni toping va yozing.
2. `/newbot` buyrug'ini yuboring.
3. Bot uchun nom bering (masalan: `Qassob Buyurtma`).
4. Bot uchun username bering — oxiri `bot` bilan tugashi kerak (masalan: `qassob_buyurtma_bot`).
5. BotFather sizga **token** beradi, masalan:
   `123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`
   Bu tokenni saqlab qo'ying — hech kimga bermang.

## 2-QADAM: Admin guruh yaratish

1. Telegramda yangi **guruh** yarating (masalan: "Qassoblik buyurtmalari").
2. Yaratgan botingizni shu guruhga a'zo qilib qo'shing.
3. Botni guruhda **admin** qiling (Settings → Administrators → botni qo'shing).
4. Guruhda istalgan bitta xabar yozing (masalan "salom") — bu keyingi qadam uchun kerak.

## 3-QADAM: Guruh chat_id sini topish

Bu loyihada `get_chat_id.py` degan yordamchi fayl bor. Uni quyidagicha ishlatasiz:

```bash
pip install -r requirements.txt
cp .env.example .env
# .env faylini ochib, BOT_TOKEN qatoriga o'z tokeningizni yozing
python get_chat_id.py
```

Konsolda guruh nomi va `chat_id` (masalan `-1001234567890`) chiqadi.
Shu raqamni `.env` faylidagi `GROUP_CHAT_ID` qatoriga yozing.

## 4-QADAM: Botni kompyuteringizda sinab ko'rish (ixtiyoriy)

```bash
pip install -r requirements.txt
python bot.py
```

Endi Telegramda botingizga `/start`, keyin `/order` yozib, to'liq suhbatni sinab ko'ring.
Yuborilgan ma'lumot admin guruhga tushishi kerak.

---

## 5-QADAM: Botni doimiy ishlaydigan qilish (hosting)

Bot ishlashi uchun kompyuter/server **24/7 yoniq** turishi kerak. Eng oson yo'l — **Railway.app**
xizmatidan foydalanish (bepul boshlanadi, kredit karta shart emas).

### Railway orqali joylashtirish

1. [github.com](https://github.com) da bepul akkaunt oching (agar yo'q bo'lsa).
2. Yangi repository (masalan `qassob-bot`) yarating va shu papkadagi barcha fayllarni
   (`bot.py`, `requirements.txt`, `Procfile`, `get_chat_id.py`) shu repoga yuklang.
   > **Muhim:** `.env` faylini GitHub'ga YUKLAMANG — u sizning maxfiy tokeningizni saqlaydi.
3. [railway.app](https://railway.app) ga o'ting, GitHub akkauntingiz orqali kiring.
4. **"New Project" → "Deploy from GitHub repo"** ni tanlang va yaratgan repongizni tanlang.
5. Loyiha ochilgach, **"Variables"** bo'limiga o'ting va ikkita o'zgaruvchi qo'shing:
   - `BOT_TOKEN` = sizning tokeningiz
   - `GROUP_CHAT_ID` = topgan chat_id raqamingiz
6. Railway avtomatik ravishda `requirements.txt` ni o'rnatadi va `Procfile` dagi
   `worker: python bot.py` buyrug'i orqali botni ishga tushiradi.
7. Bir necha daqiqadan so'ng bot 24/7 ishlay boshlaydi — endi kompyuteringizni yoqib
   qo'yish shart emas.

### Muqobil variantlar

- **Arzon VPS** (Timeweb, Beget, DigitalOcean va h.k., oyiga ~$3-5): bot kodini serverga
  yuklab, `screen` yoki `systemd` orqali doimiy ishlatish mumkin. Bu ko'proq nazoratni beradi,
  lekin biroz texnik bilim talab qiladi.
- **Fly.io**: Railway'ga o'xshash, bepul limiti bor.

Agar xohlasangiz, sizga aynan Railway bo'yicha ekran-ekran (skrinshot bilan) yordam bera olaman —
shunchaki qaysi bosqichda qiynalayotganingizni ayting.

---

## Botni qanday kengaytirish mumkin

- Har bir buyurtmaga avtomatik raqam (order ID) qo'shish.
- Mijozga "buyurtma qabul qilindi" xabaridan keyin taxminiy narxni ko'rsatish.
- Guruh o'rniga bir vaqtning o'zida Google Sheets'ga ham yozib borish (keyinroq statistikani
  ko'rish uchun qulay).
- "Buyurtma tarixi" — mijoz o'z oldingi buyurtmalarini ko'ra olishi.

Agar shulardan birortasi kerak bo'lsa, ayting — qo'shib beraman.

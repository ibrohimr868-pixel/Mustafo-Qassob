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

## Yangi imkoniyatlar: Google Sheets + yaqin manzillarni guruhlash

Endi bot ixtiyoriy ravishda har bir buyurtmani **Google Sheets** jadvaliga ham yozib boradi
(koordinatalari bilan), va admin guruhda **/hisobot** deb yozsangiz, bot bugungi
buyurtmalarni bir-biriga yaqin joylashgan mijozlarga guruhlab beradi — yetkazib beruvchi
shu tartibda borsa qulay bo'ladi.

### Google Sheets'ni ulash (5 daqiqa, kod yozish shart emas)

1. [sheets.google.com](https://sheets.google.com) da yangi bo'sh jadval yarating, nom bering
   (masalan "Qassob buyurtmalari").
2. Yuqoridagi menyudan **Extensions → Apps Script** ni tanlang.
3. Ochilgan oynadagi barcha namuna kodni o'chirib, o'rniga shu loyihadagi **Code.gs**
   faylining to'liq mazmunini joylashtiring.
4. Yuqorida disket (💾) belgisini bosib saqlang.
5. O'ng yuqoridagi ko'k **"Deploy" → "New deployment"** tugmasini bosing.
6. Type sifatida **"Web app"** ni tanlang. "Execute as": **Me**. "Who has access": **Anyone**.
7. **"Deploy"** tugmasini bosing, Google ruxsat so'raydi — "Authorize access" orqali
   o'z Google akkauntingiz bilan tasdiqlang (bu sizning shaxsiy skriptingiz, xavfsiz).
8. Chiqqan **Web app URL** (masalan `https://script.google.com/macros/s/.../exec`)
   ni nusxalab oling.
9. Railway'da **Variables** bo'limiga yangi o'zgaruvchi qo'shing:
   `SHEET_WEBHOOK_URL` = shu havola.

Shu bilan tugadi — endi har bir buyurtma avtomatik jadvalga tushadi, va telefoningizda
Google Sheets ilovasi orqali istalgan vaqt ko'rishingiz mumkin.

### /hisobot buyrug'i

Admin guruhingizda **/hisobot** deb yozsangiz, bot bugungi barcha buyurtmalarni
lokatsiyasi (koordinatasi) bo'yicha bir-biriga yaqin (1.5 km radiusda) turgan
guruhlarga bo'lib chiqarib beradi. Faqat mijoz "📍 Lokatsiyani yuborish" tugmasi
orqali joylashuvini yuborgan buyurtmalar aniq guruhlanadi; qo'lda yozilgan manzillar
alohida ro'yxatda ko'rsatiladi.

Radiusni o'zgartirish uchun `bot.py` faylida `CLUSTER_RADIUS_KM = 1.5` qatorini toping
va xohlagan kilometringizga o'zgartiring.

### Go'sht ro'yxatini o'zgartirish

`bot.py` faylida `MEAT_TYPES` ro'yxatini toping:

```python
MEAT_TYPES = [
    "🐄 Mol go'shti",
    "🐑 Qo'y go'shti",
    "🐔 Tovuq go'shti",
    "🍖 Jigar / ichki a'zolar",
    "✍️ Boshqa",
]
```

Istalgan qatorni o'chirish yoki yangi qator (masalan `"🍗 Qanot"`) qo'shish orqali
ro'yxatni o'zgartirasiz. O'zgartirgach, GitHub'da bot.py ni yangilang — Railway
avtomatik qayta ishga tushadi.

### Buyurtma tugmasi

Endi mijozlar `/order` buyrug'ini eslab yurishi shart emas — bot `/start` bosilganda
pastda doimiy **"🛒 Buyurtma berish"** tugmasini ko'rsatadi. `/order` va `/buyurtma`
buyruqlari ham hali ishlayveradi (zaxira sifatida).

---

## Yangi imkoniyatlar (2-versiya): Savatcha, mijoz xotirasi, saqlangan manzillar

Bot endi ancha "aqlli":

- **Mijozni eslab qoladi** — ism va telefon faqat birinchi marta so'raladi. Keyingi
  safar mijoz botga yozganda, bot uni tanib, to'g'ridan-to'g'ri mahsulot tanlashga o'tkazadi.
- **Saqlangan manzillar** — mijoz avval yuborgan har bir manzil ro'yxatda saqlanadi.
  Keyingi safar shu ro'yxatdan bitta manzilni tanlaydi (qayta lokatsiya yuborishi shart
  emas), yoki xohlasa yangi manzil qo'shishi mumkin.
- **Savatcha** — mijoz bir nechta mahsulotni (masalan mol go'shti HAM, qo'y go'shti HAM)
  bitta buyurtmaga qo'sha oladi.
- **"⬅️ Orqaga" tugmasi** — har bir bosqichda fikridan qaytishi mumkin (masalan
  noto'g'ri go'sht turini tanlagan bo'lsa).
- **Yakuniy tasdiqlash** — buyurtma yuborilishidan oldin mijoz butun ro'yxatni ko'rib,
  "✅ Tasdiqlash" tugmasi bilan yakunlaydi.

### ⚠️ MUHIM: eski Google Sheets jadvalingiz bo'lsa

Bu versiyada "Buyurtmalar" jadvalining ustunlari o'zgargan (endi barcha mahsulotlar
bitta "Mahsulotlar" ustunida birlashtiriladi) va yangi "Mijozlar" jadvali qo'shildi.

Agar avval sozlagan Google Sheets jadvalingiz bo'lsa:
1. Jadvalingizni oching, pastdagi **"Buyurtmalar"** varag'ini (tab) o'ng tugma bilan
   bosib **"Delete"** qiling (agar unda muhim eski ma'lumot bo'lmasa).
2. **Code.gs** kodini shu loyihadagi yangi versiyasi bilan almashtiring (Extensions →
   Apps Script → eski kodni o'chirib, yangisini joylashtiring → saqlang).
3. Boshqa hech narsa qilish shart emas — bot birinchi buyurtmada "Buyurtmalar" va
   "Mijozlar" varaqlarini o'zi qaytadan to'g'ri ustunlar bilan yaratadi.

Agar hali Google Sheets sozlamagan bo'lsangiz, yuqoridagi "Google Sheets'ni ulash"
bo'limidagi qadamlarni bajaring — u yerda ko'rsatilgan Code.gs allaqachon yangi versiya.

---

## Yangi imkoniyat (3-versiya): Fikr-mulohaza / Shikoyat

Mijozlar endi "💬 Fikr-mulohaza / Shikoyat" tugmasi orqali izoh qoldirishi mumkin.
Bu izohlar **alohida guruhga** boradi — buyurtmalar bilan aralashmaydi.

1. Yangi Telegram guruh yarating (masalan "Fikr-mulohazalar"), botni admin qilib qo'shing.
2. Guruh ID sini avvalgidek `getUpdates` havolasi orqali toping (README boshidagi
   "3-QADAM" bo'limiga qarang, xuddi shu usul).
3. Railway'da **Variables** ga yangi o'zgaruvchi qo'shing:
   `FEEDBACK_GROUP_CHAT_ID` = topgan ID raqami.

Shu bilan tayyor — mijoz yozgan har bir fikr-mulohaza shu guruhga, mijoz ismi va
(agar avval buyurtma bergan bo'lsa) telefon raqami bilan birga tushadi.

---

## Botni qanday kengaytirish mumkin

- Har bir buyurtmaga avtomatik raqam (order ID) qo'shish.
- Mijozga "buyurtma qabul qilindi" xabaridan keyin taxminiy narxni ko'rsatish.
- Guruh o'rniga bir vaqtning o'zida Google Sheets'ga ham yozib borish (keyinroq statistikani
  ko'rish uchun qulay).
- "Buyurtma tarixi" — mijoz o'z oldingi buyurtmalarini ko'ra olishi.

Agar shulardan birortasi kerak bo'lsa, ayting — qo'shib beraman.

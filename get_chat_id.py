"""
Guruhning chat_id raqamini topish uchun yordamchi skript.

QO'LLANMA:
1. Botni guruhga qo'shing va ADMIN qiling.
2. Guruhda istalgan xabar yozing (masalan "salom").
3. Shu skriptni ishga tushiring: python get_chat_id.py
4. Konsolda chiqqan "id" raqamini GROUP_CHAT_ID sifatida .env fayliga yozing
   (odatda -100 bilan boshlanadigan manfiy raqam bo'ladi).
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN topilmadi. .env faylida BOT_TOKEN ni sozlang.")

url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
response = requests.get(url).json()

if not response.get("result"):
    print("Hech qanday xabar topilmadi. Guruhda avval biror xabar yozing, keyin qayta urinib ko'ring.")
else:
    for update in response["result"]:
        message = update.get("message") or update.get("channel_post")
        if message and message.get("chat"):
            chat = message["chat"]
            print(f"Nomi: {chat.get('title', chat.get('first_name'))} | chat_id: {chat.get('id')}")

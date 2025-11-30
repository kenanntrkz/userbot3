from telethon import TelegramClient, events
from telethon.sessions import StringSession          # ← BUNU EKLE
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
import time
import requests
import json
import base64
import os                                           # ← BUNU EKLE

print("### JARVIS USERBOT v3 (MEDIA + BASE64 + FİLTRE) ###")

api_id = 36281618
api_hash = "10b562fdb21aea54e5eddf8e668957d5"

WEBHOOK_URL = "https://n8n.kenanturkoz.cloud/webhook-test/jarvis-telegram"

SESSION_STRING = os.getenv("SESSION_STRING")

def create_client():
    return TelegramClient(StringSession(SESSION_STRING), api_id, api_hash)

client = create_client()        # ← SADECE BU KALSIN

ALLOWED_CHAT_IDS = [
    -1003159248444,  # BVI Grubu
    7749345491,      # Necmettin DM
    1254096186,      # Zehra
    8544734996,      # Annem
    -5026911621,     # TeacherPAL (isteğe bağlı)
]


@client.on(events.NewMessage())
async def handler(event):

    # TELETHON MEDYA BUG-FIX
    real_media = event.media or getattr(event.message, "media", None)

    chat = await event.get_chat()
    chat_id = chat.id

    print(f"\n{'='*70}")
    print(f"🔔 YENİ MESAJ GELDİ")
    print(f"Chat ID: {chat_id}")
    print(f"Sender ID: {event.sender_id}")
    print(f"Medya var mı? {real_media is not None}")
    print("="*70)

    if chat_id not in ALLOWED_CHAT_IDS:
        print("⏭️ Bu chat izin listesinde değil.")
        return

    chat_name = getattr(chat, "title", getattr(chat, "first_name", "Bilinmeyen Sohbet"))
    text = event.raw_text or ""
    sender_id = event.sender_id
    message_id = event.id
    date = event.date

    # ===== FİLTRELEME KURALLARI =====
    # BVI GRUBU → Sadece Necmettin
    if chat_id == -1003159248444:  # BVI
        if sender_id != 7749345491:  # Necmettin değilse
            print("⏭️  BVI grubunda ama gönderen Necmettin değil, atlanıyor.")
            return

    # TeacherPAL grubu → İstersen filtre ekle
    # if chat_id == -5026911621:  # TeacherPAL
    #     # Örnek: sadece belirli kişilerden kabul et
    #     pass

    print(f"✅ Filtreyi geçti: {chat_name}")

    payload = {
        "chat_id": chat_id,
        "chat_name": chat_name,
        "sender_id": sender_id,
        "message_id": message_id,
        "text": text,
        "date": str(date),
        "has_media": False,
        "media_type": None,
        "file_name": None,
        "mime_type": None,
        "file_size": None,
        "file_base64": None,
        "has_link": False,
        "links": []
    }

    # 1) MEDYA ANALİZİ + İNDİRME + BASE64
    if real_media:
        payload["has_media"] = True
        media_type_name = type(real_media).__name__
        payload["media_type"] = media_type_name

        print(f"📎 Medya tespit edildi → {media_type_name}")

        try:
            # RAW BYTES OLARAK İNDİR
            file_bytes = await client.download_media(real_media, file=bytes)

            if file_bytes:
                print(f"📥 Medya indirildi ({len(file_bytes)} bytes)")

                # BASE64'E ÇEVİR
                payload["file_base64"] = base64.b64encode(file_bytes).decode("utf-8")
                payload["file_size"] = len(file_bytes)

                # DOKÜMAN İSE DOSYA ADINI VE MIME TYPE AL
                if isinstance(real_media, MessageMediaDocument):
                    doc = real_media.document

                    for attr in doc.attributes:
                        if hasattr(attr, "file_name"):
                            payload["file_name"] = attr.file_name
                            break

                    payload["mime_type"] = doc.mime_type

                # FOTOĞRAF İSE
                if isinstance(real_media, MessageMediaPhoto):
                    payload["file_name"] = f"photo_{message_id}.jpg"
                    payload["mime_type"] = "image/jpeg"

        except Exception as e:
            print(f"❌ Medya indirilemedi: {e}")

    # 2) LINK ANALİZİ
    if event.entities:
        for e in event.entities:
            if hasattr(e, "url"):
                payload["has_link"] = True
                payload["links"].append(e.url)

    # 3) N8N'E GÖNDER
    print("\n📤 n8n'e gönderiliyor...")
    print(f"   Medya: {payload['has_media']}, Dosya: {payload.get('file_name', 'yok')}")

    try:
        resp = requests.post(WEBHOOK_URL, json=payload, timeout=15)
        print(f"✅ n8n HTTP → {resp.status_code}")
    except Exception as e:
        print(f"❌ n8n hatası: {e}")

    print()


while True:
    try:
        print("\n" + "="*70)
        print("🤖 JARVIS USERBOT BAŞLATILIYOR")
        print("="*70)
        print(f"🌐 Webhook: {WEBHOOK_URL}\n")
        client.start()
        client.run_until_disconnected()

    except KeyboardInterrupt:
        print("\n🛑 Kullanıcı durdurdu.")
        break

    except Exception as e:
        print(f"❌ Hata: {e}")
        print("⏳ 10 saniye sonra yeniden başlatılıyor...")

        time.sleep(10)

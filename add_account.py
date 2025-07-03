from pyrogram import Client

API_ID = 29698707
API_HASH = "22b012816bcf16d58d826e6e3606a273"

print("📞 شماره اکانت را با +98 وارد کنید:")
phone = input("شماره: ").strip()
session_name = phone.replace("+", "")

app = Client(session_name, api_id=API_ID, api_hash=API_HASH)

with app:
    try:
        app.send_code(phone_number=phone)
        code = input("📨 کد تایید دریافتی در تلگرام را وارد کنید: ")
        app.sign_in(phone_number=phone, phone_code=code)
        print(f"✅ اکانت {phone} با موفقیت اضافه شد و فایل session ذخیره شد.")
    except Exception as e:
        print(f"❌ خطا: {e}")

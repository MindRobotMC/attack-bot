# ربات مدیریت اکانت‌ها و اتک تلگرام - MC

## توضیحات

این ربات تلگرام برای مدیریت پیشرفته اکانت‌های تلگرام، ثبت گروه‌های هدف اتک و گرفتن آمار ارسال‌ها طراحی شده است.  
امکانات اصلی:
- اضافه کردن اکانت‌های تلگرام با ورود کد تایید
- مشاهده لیست اکانت‌ها همراه با وضعیت ریپورت
- ثبت گروه‌های هدف برای اتک
- مشاهده گروه‌های اتک زده شده و نشده
- گرفتن لیست یوزرنیم اعضای فعال چت بر اساس تعداد پیام ارسالی
- نمایش آمار ارسال‌ها به صورت روزانه، هفتگی، ماهانه و سالانه

## پیش‌نیازها

- Python 3.9+
- کتابخانه‌های مورد نیاز (از فایل `requirements.txt` نصب کنید)

## نصب و راه‌اندازی

1. کلون یا دانلود پروژه  
2. نصب کتابخانه‌ها:
    ```bash
    pip install -r requirements.txt
    ```
3. وارد کردن اطلاعات ربات و API تلگرام در فایل کد:
    - `BOT_TOKEN` توکن ربات تلگرام
    - `API_ID` و `API_HASH` از سایت my.telegram.org
    - `OWNER_ID` آی‌دی عددی تلگرام شما (ادمین ربات)
4. اجرای ربات:
    ```bash
    python bot.py
    ```

## نحوه استفاده

- تنها مالک (OWNER_ID) اجازه دسترسی به ربات را دارد.  
- با دستور `/start` منوی اصلی نمایش داده می‌شود.  
- برای اضافه کردن اکانت، از منوی "➕ اضافه کردن اکانت" استفاده کنید.  
- برای ثبت گروه اتک جدید، از منوی اتک گزینه "➕ ثبت گروه جدید" را انتخاب کنید.  
- برای دریافت لیست اعضای فعال چت، گزینه مربوطه را انتخاب و لینک گروه را ارسال کنید.  
- آمار ارسال‌ها را می‌توانید در بخش آمار مشاهده کنید.

## فایل‌های داده

- `helpers.json` : اطلاعات اکانت‌های ذخیره شده  
- `attack_groups.json` : گروه‌های ثبت شده برای اتک  
- `stats.json` : آمار ارسال پیام‌ها

## نکات مهم

- فقط آی‌دی عددی OWNER_ID اجازه استفاده از ربات را دارد.  
- ربات به صورت خودکار فایل‌های داده را ایجاد می‌کند اگر موجود نباشند.  
- قسمت گرفتن لیست اعضای فعال چت با توجه به تعداد پیام ارسال شده قابل تنظیم است.

## پشتیبانی

برای ارتباط با سازنده ربات: [@mindrobotmc](https://t.me/mindrobotmc)

---

© 2025 MC Bot Team

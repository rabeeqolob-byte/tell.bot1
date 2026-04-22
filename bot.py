import os
import json
import uuid
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from docx import Document

# 🔑 التوكن
TOKEN = "8516814182:AAF5BKANWl0s_RBSbI_87aJNrxfF-wQ1WG4"

# 👑 الأدمن
ADMIN_ID = 6307427506

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

DATA_PATH = "data"
USERS_FILE = "users.json"
paths_map = {}

# ------------------ المستخدمين ------------------
def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f)

# ------------------ قراءة docx ------------------
def read_docx(file_path):
    doc = Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

# ------------------ بناء الأزرار ------------------
def build_keyboard(path):
    keyboard = InlineKeyboardMarkup(row_width=2)

    if not os.path.exists(path):
        os.makedirs(path)

    items = sorted(os.listdir(path))

    for item in items:
        full_path = os.path.join(path, item)
        key = str(uuid.uuid4())
        paths_map[key] = full_path

        # 📁 مجلد
        if os.path.isdir(full_path):
            keyboard.insert(
                InlineKeyboardButton(f"📁 {item}", callback_data=f"dir|{key}")
            )

        # 📄 ملفات بدون لاحقة
        elif item.endswith(".docx"):
            name = item.replace(".docx", "")
            keyboard.insert(
                InlineKeyboardButton(f"📘 {name}", callback_data=f"file|{key}")
            )

        elif item.endswith(".txt"):
            name = item.replace(".txt", "")
            keyboard.insert(
                InlineKeyboardButton(f"📄 {name}", callback_data=f"file|{key}")
            )

    return keyboard

# ------------------ /start ------------------
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    save_user(message.from_user.id)

    if message.from_user.id == ADMIN_ID:
        count = len(load_users())
        text = (
            "👑 <b>لوحة الأدمن</b>\n"
            f"👥 المستخدمين: <b>{count}</b>\n\n"
            "📂 اختر القسم"
        )
    else:
        text = "📿 <b>بوت الأدعية</b>\n📂 اختر القسم"

    await message.answer(
        text,
        reply_markup=build_keyboard(DATA_PATH),
        parse_mode="HTML"
    )

# ------------------ التعامل مع الأزرار ------------------
@dp.callback_query_handler()
async def handle(callback: types.CallbackQuery):
    await callback.answer()

    action, key = callback.data.split("|")
    path = paths_map.get(key)

    if not path:
        await callback.message.answer("❌ خطأ في المسار")
        return

    # 📁 مجلد
    if action == "dir":
        await callback.message.edit_text(
            f"📂 <b>{os.path.basename(path)}</b>",
            reply_markup=build_keyboard(path),
            parse_mode="HTML"
        )

    # 📄 ملف
    elif action == "file":
        try:
            if path.endswith(".docx"):
                text = read_docx(path)
            else:
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()

            if not text.strip():
                text = "⚠️ الملف فارغ"

            # 📌 اسم الملف
            await bot.send_message(
                callback.from_user.id,
                f"📄 <b>{os.path.basename(path).replace('.docx','').replace('.txt','')}</b>",
                parse_mode="HTML"
            )

            # 📩 المحتوى
            for i in range(0, len(text), 4000):
                await bot.send_message(
                    callback.from_user.id,
                    text[i:i+4000],
                    parse_mode="HTML"
                )

            # 📂 إعادة عرض القائمة الرئيسية بعد الملف
            await bot.send_message(
                callback.from_user.id,
                "📂 <b>القائمة الرئيسية</b>",
                reply_markup=build_keyboard(DATA_PATH),
                parse_mode="HTML"
            )

        except Exception as e:
            await callback.message.answer(f"❌ خطأ: {e}")

# ------------------ تشغيل ------------------
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

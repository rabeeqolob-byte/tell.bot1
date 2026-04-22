import os
import json
import uuid
import asyncio
from docx import Document

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

# 🔑 التوكن
TOKEN = os.getenv("BOT_TOKEN")

# 👑 الأدمن
ADMIN_ID = 6307427506

bot = Bot(token=TOKEN)
dp = Dispatcher()

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

# ------------------ الأزرار ------------------
def build_keyboard(path):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    if not os.path.exists(path):
        os.makedirs(path)

    items = sorted(os.listdir(path))

    for item in items:
        full_path = os.path.join(path, item)
        key = str(uuid.uuid4())
        paths_map[key] = full_path

        if os.path.isdir(full_path):
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(text=f"📁 {item}", callback_data=f"dir|{key}")
            ])
        elif item.endswith(".docx"):
            name = item.replace(".docx", "")
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(text=f"📘 {name}", callback_data=f"file|{key}")
            ])
        elif item.endswith(".txt"):
            name = item.replace(".txt", "")
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(text=f"📄 {name}", callback_data=f"file|{key}")
            ])

    return keyboard

# ------------------ /start ------------------
@dp.message(F.text == "/start")
async def start(message: Message):
    save_user(message.from_user.id)

    if message.from_user.id == ADMIN_ID:
        count = len(load_users())
        text = f"👑 أهلاً بك\n👥 المستخدمين: {count}\n📂 اختر قسم"
    else:
        text = "📿 أهلاً بك في البوت\n📂 اختر قسم"

    await message.answer(text, reply_markup=build_keyboard(DATA_PATH))

# ------------------ الأزرار ------------------
@dp.callback_query()
async def handler(callback: CallbackQuery):
    await callback.answer()

    action, key = callback.data.split("|")
    path = paths_map.get(key)

    if not path:
        await callback.message.answer("❌ خطأ")
        return

    # 📁 مجلد
    if action == "dir":
        await callback.message.edit_text(
            f"📂 {os.path.basename(path)}",
            reply_markup=build_keyboard(path)
        )

    # 📄 ملف
    elif action == "file":
        if path.endswith(".docx"):
            text = read_docx(path)
        else:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()

        if not text.strip():
            text = "فارغ"

        await callback.message.answer(f"📄 {os.path.basename(path)}")

        for i in range(0, len(text), 4000):
            await callback.message.answer(text[i:i+4000])

        # 📂 إعادة القائمة
        await callback.message.answer(
            "📂 القائمة الرئيسية",
            reply_markup=build_keyboard(DATA_PATH)
        )

# ------------------ تشغيل ------------------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

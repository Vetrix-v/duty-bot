import json
import os
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz

# --- НАСТРОЙКИ ---
BOT_TOKEN = "8970126433:AAFXVc3NrSKUP17vDXD6ItIbvzmsx_UOa8g"
CHAT_ID = -1004428137606             # ID группы (с минусом)
ADMIN_ID = 5152504148                # Твой личный ID
TIMEZONE = "Europe/Kyiv"
DUTY_FILE = "duty_data.json"

DAYS_UA = {
    0: "понеділок",
    1: "вівторок",
    2: "середа",
    3: "четвер",
    4: "п'ятниця",
    5: "субота",
    6: "неділя"
}

STUDENTS_LIST = [
    "Бізоня Олександр Олександрович",
    "Богдан Давид Олександрович",
    "Васько Аліна Іванівна",
    "Галушка Максим Олегович",
    "Густей Юрій Юрійович",
    "Кисельов Артем Олександрович",
    "Кінаш Марко Михайлович",
    "Клим Аліна Михайлівна",
    "Кротов Артем Вікторович",
    "Кузьма Валдим Русланович",
    "Куриліч Станіслав Романович",
    "Лесних Софія Іванівна",
    "Лінда Поліна Андріївна",
    "Макарович Анастасія Іванівна",
    "Мечержак Ростислав Мар'янович",
    "Мілоян Герман Романович",
    "Огарь Віктор Олександрович",
    "Оксьоненко Давид Олегович",
    "Опаненко Орисла Олександрівна",
    "Пирко Іван Дмитрович",
    "Пічкар Ділан Русланович",
    "Тітова Анна Гнатівна",
    "Тромчак Іван Іванович",
    "Ходанич Артем Павлович",
    "Цибик Богдан Євгенович",
    "Черепаня Давид Іванович",
    "Чубаров Андрій Максимович",
    "Шаталова Люна Сергіївна",
    "Шевляков Станіслав Валентинович",
    "Шелевер Макар Віталійович",
    "Ярема Анастасія Василівна",
    "Ященко Владислав Євгенович"
]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler(timezone=pytz.timezone(TIMEZONE))

def load_data():
    if not os.path.exists(DUTY_FILE):
        data = {
            "students": STUDENTS_LIST,
            "current_index": 2
        }
        save_data(data)
        return data
    with open(DUTY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DUTY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_main_admin_keyboard(idx):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Чергував(-ла)", callback_data=f"done_{idx}"),
            InlineKeyboardButton(text="❌ Відсутній(-ня) (заміна)", callback_data=f"absent_{idx}")
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="shift_prev"),
            InlineKeyboardButton(text="Вперед ➡️", callback_data="shift_next")
        ],
        [
            InlineKeyboardButton(text="👥 Обрати іншого чергового", callback_data="select_page_0")
        ]
    ])

async def send_daily_duty():
    data = load_data()
    students = data.get("students", [])
    if not students:
        return

    idx = data.get("current_index", 0) % len(students)
    student = students[idx]

    now = datetime.now(pytz.timezone(TIMEZONE))
    day_name = DAYS_UA.get(now.weekday(), "")
    date_str = now.strftime("%d.%m.%Y")

    group_text = "🔔 <b>Чергування на день</b>\n\n📅 Сьогодні: <b>" + day_name.capitalize() + "</b>, <b>" + date_str + "</b>\n🧹 Черговий(-а): <b>" + student + "</b>\n\nГарного навчального дня!"
    await bot.send_message(CHAT_ID, group_text, parse_mode="HTML")

    try:
        admin_text = "📋 <b>Чергування на сьогодні (" + date_str + ")</b>\n\nПризначено: <b>" + student + "</b>\nОберіть дію:"
        await bot.send_message(ADMIN_ID, admin_text, reply_markup=get_main_admin_keyboard(idx), parse_mode="HTML")
    except Exception as e:
        print("Помилка відправки адміну:", e)

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    data = load_data()
    students = data.get("students", [])
    idx = data.get("current_index", 0) % len(students)
    student = students[idx]

    text = "⚙️ <b>Панель керування черговими</b>\n\n📌 Поточний черговий: <b>" + student + "</b> (номер " + str(idx + 1) + "/" + str(len(students)) + ")"
    await message.answer(text, reply_markup=get_main_admin_keyboard(idx), parse_mode="HTML")

@dp.message(Command("duty"))
async def cmd_duty(message: types.Message):
    data = load_data()
    students = data.get("students", [])
    if not students:
        await message.answer("Список порожній.")
        return
    idx = data.get("current_index", 0) % len(students)
    now = datetime.now(pytz.timezone(TIMEZONE))
    day_name = DAYS_UA.get(now.weekday(), "")
    date_str = now.strftime("%d.%m.%Y")

    text = "📅 Сьогодні: <b>" + day_name.capitalize() + "</b>, " + date_str + "\n🧹 Черговий(-а): <b>" + students[idx] + "</b>"
    await message.answer(text, parse_mode="HTML")

@dp.message(Command("list"))
async def cmd_list(message: types.Message):
    data = load_data()
    students = data.get("students", [])
    idx = data.get("current_index", 0) % len(students) if students else -1

    lines = []
    for i, name in enumerate(students):
        marker = "👉 " if i == idx else "   "
        lines.append(marker + str(i + 1) + ". " + name)

    text = "📋 <b>Список чергових:</b>\n\n" + "\n".join(lines)
    await message.answer(text, parse_mode="HTML")

@dp.message(Command("id"))
async def cmd_id(message: types.Message):
    await message.answer("ID цього чату: <code>" + str(message.chat.id) + "</code>", parse_mode="HTML")

@dp.callback_query(F.data.startswith("done_"))
async def process_duty_done(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    data = load_data()
    students = data.get("students", [])
    idx = data.get("current_index", 0) % len(students)
    student = students[idx]

    data["current_index"] = (idx + 1) % len(students)
    save_data(data)

    new_idx = data["current_index"]
    text = "✅ <b>Підтверджено:</b> " + student + " почергував(-ла).\n\n📌 Наступний у черзі: <b>" + students[new_idx] + "</b>"
    await callback.message.edit_text(text, reply_markup=get_main_admin_keyboard(new_idx), parse_mode="HTML")
    await callback.answer("Чергування зараховано!")

@dp.callback_query(F.data.startswith("absent_"))
async def process_duty_absent(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    data = load_data()
    students = data.get("students", [])
    idx = data.get("current_index", 0) % len(students)
    next_idx = (idx + 1) % len(students)

    absent = students[idx]
    substitute = students[next_idx]

    students[idx], students[next_idx] = students[next_idx], students[idx]
    save_data(data)

    admin_msg = "❌ <b>Заміну виконано:</b>\n<s>" + absent + "</s> відсутній(-ня).\n🧹 Чергує сьогодні: <b>" + substitute + "</b>\n\n<i>(" + absent + " помінявся місцями і чергуватиме наступним)</i>"
    await callback.message.edit_text(admin_msg, reply_markup=get_main_admin_keyboard(idx), parse_mode="HTML")
    await callback.answer("Заміну проведено!")

    alert_text = "⚠️ <b>Увага! Зміна чергового</b>\n\nСьогодні чергує: <b>" + substitute + "</b> замість " + absent + " 🧹"
    await bot.send_message(CHAT_ID, alert_text, parse_mode="HTML")

@dp.callback_query(F.data.in_(["shift_next", "shift_prev"]))
async def process_shift(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    data = load_data()
    students = data.get("students", [])
    idx = data.get("current_index", 0)

    if callback.data == "shift_next":
        idx = (idx + 1) % len(students)
    else:
        idx = (idx - 1) % len(students)

    data["current_index"] = idx
    save_data(data)

    text = "⚙️ <b>Панель керування черговими</b>\n\n📌 Поточний черговий: <b>" + students[idx] + "</b> (номер " + str(idx + 1) + "/" + str(len(students)) + ")"
    await callback.message.edit_text(text, reply_markup=get_main_admin_keyboard(idx), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data.startswith("select_page_"))
async def process_select_page(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    page = int(callback.data.split("_")[2])
    data = load_data()
    students = data.get("students", [])
    per_page = 8
    total_pages = (len(students) + per_page - 1) // per_page

    start = page * per_page
    end = min(start + per_page, len(students))

    buttons = []
    for i in range(start, end):
        parts = students[i].split()
        short_name = parts[0] + " " + parts[1] if len(parts) >= 2 else students[i]
        buttons.append([InlineKeyboardButton(text=str(i + 1) + ". " + short_name, callback_data="set_duty_" + str(i))])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data="select_page_" + str(page - 1)))
    nav.append(InlineKeyboardButton(text=str(page + 1) + "/" + str(total_pages), callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="➡️", callback_data="select_page_" + str(page + 1)))
    buttons.append(nav)
    buttons.append([InlineKeyboardButton(text="🔙 Назад до меню", callback_data="back_to_menu")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text("Оберіть студента, якого призначити черговим:", reply_markup=kb)
    await callback.answer()

@dp.callback_query(F.data.startswith("set_duty_"))
async def process_set_duty(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    new_idx = int(callback.data.split("_")[2])
    data = load_data()
    students = data.get("students", [])

    data["current_index"] = new_idx
    save_data(data)

    text = "✅ <b>Чергового успішно змінено!</b>\n\n📌 Тепер призначено: <b>" + students[new_idx] + "</b>"
    await callback.message.edit_text(text, reply_markup=get_main_admin_keyboard(new_idx), parse_mode="HTML")
    await callback.answer("Призначено!")

@dp.callback_query(F.data == "back_to_menu")
async def process_back_to_menu(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    data = load_data()
    students = data.get("students", [])
    idx = data.get("current_index", 0) % len(students)

    text = "⚙️ <b>Панель керування черговими</b>\n\n📌 Поточний черговий: <b>" + students[idx] + "</b> (номер " + str(idx + 1) + "/" + str(len(students)) + ")"
    await callback.message.edit_text(text, reply_markup=get_main_admin_keyboard(idx), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "noop")
async def process_noop(callback: types.CallbackQuery):
    await callback.answer()

async def main():
    scheduler.add_job(
        send_daily_duty,
        trigger="cron",
        day_of_week="mon-fri",
        hour=8,
        minute=0
    )
    scheduler.start()

    print("Бот запущений...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
import requests



def user_role_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(text="👤 Yo'lovchi", callback_data="role_passenger"),
        InlineKeyboardButton(text="🚖 Haydovchi", callback_data="role_driver"),
        InlineKeyboardButton(text="📦 Yuk beruvchi", callback_data="role_shipper")
    )
    return keyboard

def user_car_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        InlineKeyboardButton(text="Nexia2", callback_data="nexia2"),
        InlineKeyboardButton(text="Nexia3", callback_data="nexia3"),
        InlineKeyboardButton(text="Cobalt", callback_data="cobalt"),
        InlineKeyboardButton(text="Gentra", callback_data="gentra"),
        InlineKeyboardButton(text="Onix", callback_data="onix"),
        InlineKeyboardButton(text="Kia", callback_data="kia"),
        InlineKeyboardButton(text="BYD", callback_data="byd"),
        InlineKeyboardButton(text="Hyundai", callback_data="Hyundai"),
        InlineKeyboardButton(text="Captiva", callback_data="captiva")
    )
    return keyboard


def driver_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("📍 Yurish joyi tanlash"), KeyboardButton("🔢 Bo'sh joylar soni")],
            [KeyboardButton("⚙️ Sozlamalar"), KeyboardButton("📋 Barcha Buyurtmalar")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

def passenger_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("📋 Buyurtma berish"), KeyboardButton("📋 Barcha Buyurtmalar")],
            [KeyboardButton("⚙️ Sozlamalar")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

def shipper_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("📦 Yuk yuborish"), KeyboardButton("📋 Barcha Buyurtmalar")],
            [KeyboardButton("⚙️ Sozlamalar")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
def direction_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(text=f"Toshkent -> Vodiy", callback_data="toshkent_vodiy"),
        InlineKeyboardButton(text=f"Vodiy -> Toshkent", callback_data="vodiy_toshkent")
    )
    return keyboard


def vodiy_region_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(text=f"Namangan", callback_data="namangan"),
        InlineKeyboardButton(text=f"Farg'ona", callback_data="farg'ona"),
        InlineKeyboardButton(text=f"Andijon", callback_data="andijon")
    )
    return keyboard

def tashkent_region_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(text=f"Bektemir tumani", callback_data="bektemir"),
        InlineKeyboardButton(text=f"Chilonzor tumani", callback_data="chilonzor"),
        InlineKeyboardButton(text=f"Mirobod tumani", callback_data="mirobod"),
        InlineKeyboardButton(text=f"Mirzo Ulug'bek tumani", callback_data="mirzo_ulug'bek"),
        InlineKeyboardButton(text=f"Olmazor tumani", callback_data="olmazor"),
        InlineKeyboardButton(text=f"Sergeli tumani", callback_data="sergeli"),
        InlineKeyboardButton(text=f"Shayhontohur tumani", callback_data="shayhontohur"),
        InlineKeyboardButton(text=f"Uchtepa tumani", callback_data="uchtepa"),
        InlineKeyboardButton(text=f"Yakkasaroy tumani", callback_data="yakkassaroy"),
        InlineKeyboardButton(text=f"Yashnaobod tumani", callback_data="yashnaobod"),
        InlineKeyboardButton(text=f"Yunusobod tumani", callback_data="yunusobod")
    )
    return keyboard

def departure_time_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(text="08:00", callback_data="08:00"),
        InlineKeyboardButton(text="09:00", callback_data="09:00"),
        InlineKeyboardButton(text="10:00", callback_data="10:00"),
        InlineKeyboardButton(text="11:00", callback_data="11:00"),
        InlineKeyboardButton(text="12:00", callback_data="12:00"),
        InlineKeyboardButton(text="13:00", callback_data="13:00"),
        InlineKeyboardButton(text="14:00", callback_data="14:00"),
        InlineKeyboardButton(text="15:00", callback_data="15:00"),
        InlineKeyboardButton(text="16:00", callback_data="16:00"),
        InlineKeyboardButton(text="17:00", callback_data="17:00"),
        InlineKeyboardButton(text="18:00", callback_data="18:00"),
        InlineKeyboardButton(text="19:00", callback_data="19:00"),
        InlineKeyboardButton(text="20:00", callback_data="20:00"),
        InlineKeyboardButton(text="21:00", callback_data="21:00"),
        InlineKeyboardButton(text="22:00", callback_data="22:00"),
        InlineKeyboardButton(text="23:00", callback_data="23:00")
    )
    return keyboard

def pessenger_count_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(text="1", callback_data="1"),
        InlineKeyboardButton(text="2", callback_data="2"),
        InlineKeyboardButton(text="3", callback_data="3"),
        InlineKeyboardButton(text="4", callback_data="4"),
    )
    return keyboard
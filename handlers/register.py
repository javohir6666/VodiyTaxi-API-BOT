import re
from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from sqlalchemy.exc import IntegrityError
from utils.keyboards import user_role_keyboard, user_car_keyboard, driver_keyboard, passenger_keyboard, shipper_keyboard
from .group_order import get_user_info
import re
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.dispatcher.filters.state import State, StatesGroup
from config_data import USERS_API_URL, UPDATE_ROLE_USER_API_URL
import requests

# Foydalanuvchini ro'yxatdan o'tkazish uchun holatlar
class RegisterState(StatesGroup):
    role = State()
    car_name = State()
    car_number = State()
    phone_number = State()

# 1-BOSQICH: Foydalanuvchi rolini tanlash
async def start_registration(message: types.Message):
    user_id = message.from_user.id
    get_user = get_user_info(user_id)
    is_registered = get_user.get('is_registered')
    if is_registered == True:
        await message.answer("🟢 Siz ro'yxatdan o'tganiz! \nBotdan foydalanish uchun /start buyrug'ini yozing!")
        return
    await message.answer("Siz kim sifatida ro'yxatdan o'tmoqchisiz?", reply_markup=user_role_keyboard())
    await RegisterState.role.set()

# Foydalanuvchi rolini tanlash
async def handle_role_selection(call: types.CallbackQuery, state: FSMContext):
    role = call.data.split('_')[1]  # 'passenger' yoki 'driver' yoki 'shipper'
    user_id = call.from_user.id

    # Ma'lumotlarni vaqtinchalik holatda saqlaymiz
    await state.update_data(user_type=role)

    if role == 'driver':
        await call.message.edit_text("🚗 Mashinangiz modelini tanlang:", reply_markup=user_car_keyboard())
        await RegisterState.car_name.set()
    else:
        await call.message.edit_text("📞 Telefon raqamingizni kiriting (+998XXXXXXXXX shaklida):")
        await RegisterState.phone_number.set()
    
    await call.answer()

# 2-BOSQICH (Faqat haydovchilar uchun): Mashina modeli tanlash
async def handle_car_name(call: types.CallbackQuery, state: FSMContext):
    car_name = call.data
    await state.update_data(car_name=car_name)

    await call.message.edit_text("🚗 Mashinangiz raqamini kiriting: \nMasalan: 50A550AA ")
    await RegisterState.car_number.set()
    await call.answer()

# 3-BOSQICH (Faqat haydovchilar uchun): Mashina raqamini kiritish
async def handle_car_number(message: types.Message, state: FSMContext):
    car_number = message.text.strip()
    await state.update_data(car_number=car_number)

    await message.answer("📞 Telefon raqamingizni kiriting (+998XXXXXXXXX shaklida):")
    await RegisterState.phone_number.set()

# 4-BOSQICH: Telefon raqamini tekshirish va saqlash
async def handle_phone_number(message: types.Message, state: FSMContext):
    phone_number = message.text.strip()
    
    if not re.match(r'^\+998\d{9}$', phone_number):
        await message.reply("❌ Telefon raqami +998 bilan boshlanishi va 9 ta raqamdan iborat bo‘lishi kerak.")
        return

    await state.update_data(phone_number=phone_number)
    
    # Ma'lumotlarni olish
    data = await state.get_data()
    role = data['user_type']
    car_name = data.get('car_name')
    car_number = data.get('car_number')

    # API manzilini aniqlash
    user_data = {
        "telegram_id": message.from_user.id,
        "telegram_username": message.from_user.username,
        "telegram_fullname": message.from_user.full_name,
        "phone_number": phone_number,
        "active_role": role,  # role "driver" yoki "passenger" bo'lishi kerak
        "is_registered": True
    }
    
    try:
        # API'ga ma'lumot yuborish
        response = requests.post(USERS_API_URL, json=user_data)
              
        if response.status_code == 201 and role == 'driver':
            await message.answer("✅ Siz haydovchi sifatida muvaffaqiyatli ro'yxatdan o'tdingiz!", reply_markup=driver_keyboard())
            driver_data = {
                "user_id": user_data["telegram_id"],
                "car_name": car_name,
                "car_number": car_number
            }
            requests.patch(f"{UPDATE_ROLE_USER_API_URL}{message.from_user.id}/", json=driver_data)

        elif response.status_code == 201 and role == 'passenger':
            await message.answer("✅ Siz Yo'lovchi sifatida muvaffaqiyatli ro'yxatdan o'tdingiz!", reply_markup=passenger_keyboard())
        elif response.status_code == 201 and role == 'shipper':
            await message.answer("✅ Siz Yuk yuboruvchi sifatida muvaffaqiyatli ro'yxatdan o'tdingiz!", reply_markup=shipper_keyboard())
        else:
            await message.answer(f"❌ Ro'yxatdan o'tishda xato yuz berdi: {response.text}")
    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi: {e}")
    finally:
        await state.finish()


def register_handlers(dp: Dispatcher):
    # Registering the message handler for /register command
    dp.register_message_handler(start_registration, commands=['register'])
    
    # Registering the callback query handler for role selection
    dp.register_callback_query_handler(handle_role_selection, lambda c: c.data.startswith('role_'), state=RegisterState.role)
    
    # Registering the callback query handler for car selection (for drivers)
    dp.register_callback_query_handler(handle_car_name, lambda c: c.data in ['nexia2', 'nexia3', 'cobalt', 'gentra', 'onix', 'kia', 'byd', 'hyundai', 'captiva'], state=RegisterState.car_name)
    
    # Registering the message handlers for other steps
    dp.register_message_handler(handle_car_number, state=RegisterState.car_number)
    dp.register_message_handler(handle_phone_number, state=RegisterState.phone_number)
from aiogram import types, Dispatcher
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from utils.keyboards import direction_keyboard, tashkent_region_keyboard, vodiy_region_keyboard, changer_role_keyboard, driver_keyboard, passenger_keyboard, shipper_keyboard
import requests
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config_data import API_URL, USERS_API_URL, UPDATE_ROLE_USER_API_URL, ORDER_UPDATE_API
from .group_order import get_user_info
class DriverLocationState(StatesGroup):
    current_direction = State()
    current_region = State()
    dropoff_location = State()


async def start_location_driver(message: types.Message):
    await message.answer("↔️ Yo'nalishni tanlang:", reply_markup=direction_keyboard())
    await DriverLocationState.current_direction.set()

# **Yo'nalish tanlash**
async def handle_current_direction(call: types.CallbackQuery, state: FSMContext):
    direction = call.data
    await state.update_data(current_direction=direction)

    if direction == 'toshkent_vodiy':
        await call.message.edit_text("📍 Toshkentning qaysi tumanidasiz?", reply_markup=tashkent_region_keyboard())
    elif direction == 'vodiy_toshkent':
        await call.message.edit_text("📍 Vodiyning qaysi viloyatidasiz?", reply_markup=vodiy_region_keyboard())

    await DriverLocationState.current_region.set()
    await call.answer()


# **Hozirgi joylashuvni tanlash**
async def handle_current_region(call: types.CallbackQuery, state: FSMContext):
    region = call.data
    await state.update_data(current_region=region)

    data = await state.get_data()
    direction = data.get('current_direction')

    if direction == 'toshkent_vodiy':
        await call.message.edit_text("📍 Qaysi viloyatga yurasiz?", reply_markup=vodiy_region_keyboard())
    elif direction == 'vodiy_toshkent':
        await call.message.edit_text("📍 Toshkentning qaysi tumaniga yurasiz?", reply_markup=tashkent_region_keyboard())

    await DriverLocationState.dropoff_location.set()
    await call.answer()


# **Borish joyini tanlash va ma'lumotni bazaga yozish**
async def handle_dropoff_location(call: types.CallbackQuery, state: FSMContext):
    dropoff_location = call.data
    driver = call.from_user.id
    await state.update_data(dropoff_location=dropoff_location)

    try:
        # API'dan passenger ma'lumotlarini olish
        get_driver_id = requests.get(f"{API_URL}user/{driver}/")
        get_driver_id.raise_for_status()  # HTTP xatoliklarni tekshirish
        driver_id = get_driver_id.json().get('id')  # .get() xavfsizroq
        if not driver_id:
            raise ValueError("Haydovchi ID topilmadi")
        print(f"Yo'lovchi ID: {driver_id} ******")

    except requests.exceptions.RequestException as e:
        await call.message.edit_text(f"❌ API bilan bog'lanishda xatolik yuz berdi: {str(e)}", reply_markup=None)
        return
    except ValueError as e:
        await call.message.edit_text(f"❌ {str(e)}", reply_markup=None)
        return

    data = await state.get_data()
    driver_id = data.get('driver_id')
    direction = data.get('current_direction')
    current_region = data.get('current_region')
    dropoff_location = data.get('dropoff_location')

    driver_data = {
        "user": driver_id,
        "current_direction": direction,
        "current_region": current_region,
        "dropoff_location": dropoff_location
    }

    print(driver_data)

    try:
            # API'ga order yuborish
        response = requests.patch(f"{UPDATE_ROLE_USER_API_URL}{driver}/", json=driver_data)

        if response.status_code == 200:
            await call.message.edit_text("✅ Marshrut muvaffaqiyatli saqlandi.", reply_markup=None)
        else:
            await call.message.edit_text(f"❌ Xatolik yuz berdi: {response.status_code} - {response.text}", reply_markup=None)

    except Exception as e:
        await call.message.edit_text(f"❌ Xatolik yuz berdi: {e}", reply_markup=None)

    finally:
        # State'ni yakunlash
        await state.finish()
        await call.answer()

async def get_active_order(message: types.Message):
    driver_id = message.from_user.id
    get_driver = get_user_info(driver_id)
    driver = get_driver.get('id')
    # API'dan bajarilgan barcha orderlarni olish
    response = requests.get(f"{API_URL}driver/{driver}/active_orders/")
    response.raise_for_status()  # HTTP xatoliklarni tekshirish
    orders = response.json()
    if response.status_code == 200:
        if orders:
            for order in orders:
                message_text = (f"✅ Buyurtma raqami:{order['id']}\n\n"
                                    f"📑 Buyurtma turi: {order['order_type']}\n"
                                    f"🚖 Yo\'nalish: {order['direction']}\n"
                                    f"📍 Olish joyi: {order['pickup_location']}"
                                    f"dan → {order['dropoff_location']}ga\n"
                                    f"🕒 Ketish vaqti: {order['departure_time']}\n"
                                    )
                # Yakunlash tugmasi
                c_keyboard = InlineKeyboardMarkup()
                complate_keyboard = InlineKeyboardButton("✅ Yakunlash", callback_data=f"complate_{order['id']}")
                c_keyboard.add(complate_keyboard)
                await message.answer(message_text, reply_markup=c_keyboard)
        else:
            await message.answer("🔴 Aktiv buyurtmalar topilmadi!")

async def handle_complate_order(call: types.CallbackQuery):
    if not call.data.startswith("complate_"):
        return  # Noto'g'ri callback bo‘lsa, qaytib ketamiz
    
    order_id = call.data.split("_")[1]
    order_endpoint = f"{ORDER_UPDATE_API}{order_id}/"
    print(f"Order ID: {order_id}")
    print(order_endpoint)
    print("Handle complate order ishga tushdi")
    order_data = {
            "status": "completed"
        }
    response = requests.patch(order_endpoint, json=order_data)
    message = (f"✅ #{order_id}-sonli buyurtma yakunlandi!\n")

    if response.status_code == 200:
        await call.message.edit_text(message, reply_markup=None)
    else:
        await call.answer("❌ Xatolik yuz berdi, iltimos qayta urinib ko'ring.", show_alert=True)

# Role tanlash
async def set_role_own(message: types.Message):
    await message.answer("⚠️ Siz kim sifatida ro'yxatdan o'tmoqchisiz?", reply_markup=changer_role_keyboard())

import logging
import requests
from aiogram import types
from aiogram.types import InlineKeyboardMarkup

async def handle_set_role_own(call: types.CallbackQuery):
    if not call.data.startswith("changerole_"):
        return  # Noto'g'ri callback bo‘lsa, qaytib ketamiz
    
    role = call.data.split('_')[1]  # 'passenger', 'driver', yoki 'shipper'
    user_id = call.from_user.id
    role_endpoint = f"{UPDATE_ROLE_USER_API_URL}{user_id}/"
    role_data = {"active_role": role}
    
    response = requests.patch(role_endpoint, json=role_data)

    if response.status_code == 200:
        role_text = {
            "passenger": "✅ Siz Yo'lovchi sifatida ro'yxatdan o'tdingiz!\n🟢 Botni qayta ishga tushuring /start",
            "driver": "✅ Siz Haydovchi sifatida ro'yxatdan o'tdingiz!\n🟢 Botni qayta ishga tushuring /start",
            "shipper": "✅ Siz Yuk yuboruvchi sifatida ro'yxatdan o'tdingiz!\n🟢 Botni qayta ishga tushuring /start"
        }

        await call.message.edit_text(role_text[role])
    
    else:
        await call.answer("❌ Xatolik yuz berdi, iltimos qayta urinib ko'ring.", show_alert=True)


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(start_location_driver, commands=['location_driver'])
    dp.register_message_handler(start_location_driver, text="📍 Yurish joyi tanlash", state="*")
    dp.register_message_handler(get_active_order, commands=["active_orders"], state="*")
    dp.register_message_handler(get_active_order, text="📋 Aktiv buyurtmalar", state="*")
    dp.register_message_handler(set_role_own, commands=["set_role_own"], state="*")
    dp.register_message_handler(set_role_own, text="👤 Rolni o'zgartirish", state="*")
    dp.register_callback_query_handler(handle_current_direction, state=DriverLocationState.current_direction)
    dp.register_callback_query_handler(handle_current_region, state=DriverLocationState.current_region)
    dp.register_callback_query_handler(handle_dropoff_location, state=DriverLocationState.dropoff_location)
    dp.register_callback_query_handler(lambda c: c.data.startswith("changerole_"), handle_set_role_own)
    dp.register_callback_query_handler(lambda c: c.data.startswith("complate_"), handle_complate_order)
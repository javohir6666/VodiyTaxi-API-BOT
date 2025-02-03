from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from utils.keyboards import direction_keyboard, vodiy_region_keyboard, tashkent_region_keyboard, departure_time_keyboard, pessenger_count_keyboard
import requests
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config_data import API_URL, ORDERS_API_URL
from .group_order import send_order_to_group

class PessengerOrderState(StatesGroup):
    direction = State()
    pickup_location = State()
    dropoff_location = State()
    departure_time = State()
    passenger_count = State()
    confirm_order = State()

# Buyurtma jarayonini boshlash
async def start_order(message: types.Message):
    await message.answer("Yo'nalishni tanlang", reply_markup=direction_keyboard())
    await PessengerOrderState.direction.set()

async def handle_direction_selection(call: types.CallbackQuery, state: FSMContext):
    direction = call.data
    await state.update_data(direction=direction)

    if direction == 'toshkent_vodiy':
        await call.message.edit_text("📍 Toshkentning qaysi tumanidasiz hozir?", reply_markup=tashkent_region_keyboard())
    elif direction == 'vodiy_toshkent':
        await call.message.edit_text("📍 Vodiyning qaysi viloyatidasiz hozir?", reply_markup=vodiy_region_keyboard())

    await PessengerOrderState.pickup_location.set()
    await call.answer()

# Jo'nash joyini tanlashni qayta ishlash
async def handle_pickup_location(call: types.CallbackQuery, state: FSMContext):
    pickup_location = call.data
    await state.update_data(pickup_location=pickup_location)

    data = await state.get_data()
    direction = data.get('direction')

    if direction == 'toshkent_vodiy':
        await call.message.edit_text("📍 Vodiyning qaysi viloyatiga borasiz?:", reply_markup=vodiy_region_keyboard())
    elif direction == 'vodiy_toshkent':
        await call.message.edit_text("📍 Toshkentning qaysi tumaniga?:", reply_markup=tashkent_region_keyboard())

    await PessengerOrderState.dropoff_location.set()
    await call.answer()

# Tushish joyini tanlashni qayta ishlash
async def handle_dropoff_location(call: types.CallbackQuery, state: FSMContext):
    dropoff_location = call.data
    await state.update_data(dropoff_location=dropoff_location)

    await call.message.edit_text("📅 Ketish vaqtni tanlang:", reply_markup=departure_time_keyboard())
    await PessengerOrderState.departure_time.set()
    await call.answer()

async def handle_pickup_time(call: types.CallbackQuery, state: FSMContext):
    departure_time = call.data  # pickup_time olish
    await state.update_data(departure_time=departure_time)

    await call.message.edit_text("👥 Yo'lovchilar soni, necha kishisiz?", reply_markup=pessenger_count_keyboard())
    await PessengerOrderState.passenger_count.set()
    await call.answer()

async def handle_passenger_count(call: types.CallbackQuery, state: FSMContext):
    passenger_count = call.data
    await state.update_data(passenger_count=passenger_count)

    # Foydalanuvchi ma'lumotlari
    data = await state.get_data()
    direction = data.get('direction')
    pickup_location = data.get('pickup_location')
    dropoff_location = data.get('dropoff_location')
    departure_time = data.get('departure_time')
    passenger_count = data.get('passenger_count')

    # Buyurtma ma'lumotlarini tekshirish
    await call.message.edit_text(
        f"✅ Buyurtma ma'lumotlari:\n\n"
        f"↔️ Yo'nalish: {direction.title()}\n"
        f"📍 Jo'nash joyi: {pickup_location.title()}dan - {dropoff_location.title()}ga\n"
        f"📅 Ketish vaqti: {departure_time}\n"
        f"👥 Yo'lovchilar soni: {passenger_count}\n\n"
        f"❓ Buyurtmani tasdiqlaysizmi?",
        reply_markup=InlineKeyboardMarkup(row_width=2).add(
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_order"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_order")
        )
    )

    await PessengerOrderState.confirm_order.set()
    await call.answer()

async def handle_confirm_order(call: types.CallbackQuery, state: FSMContext):
    passenger = call.from_user.id

    try:
        # API'dan passenger ma'lumotlarini olish
        get_passenger_id = requests.get(API_URL + f"user/{passenger}/")
        get_passenger_id.raise_for_status()
        passenger_id = get_passenger_id.json().get('id')
        if not passenger_id:
            raise ValueError("Yo'lovchi ID topilmadi")
        print(f"Yo'lovchi ID: {passenger_id} ******")

    except requests.exceptions.RequestException as e:
        await call.message.edit_text(f"❌ API bilan bog'lanishda xatolik yuz berdi: {str(e)}", reply_markup=None)
        await state.finish()
        return
    except ValueError as e:
        await call.message.edit_text(f"❌ {str(e)}", reply_markup=None)
        await state.finish()
        return

    # Foydalanuvchi tomonidan saqlangan ma'lumotlarni olish
    data = await state.get_data()
    direction = data.get('direction')
    pickup_location = data.get('pickup_location')
    dropoff_location = data.get('dropoff_location')
    departure_time = data.get('departure_time')

    # Order ma'lumotlarini tayyorlash
    order_data = {
        "order_type": "passenger",
        "passenger": passenger_id,
        "direction": direction,
        "pickup_location": pickup_location,
        "dropoff_location": dropoff_location,
        "departure_time": departure_time,
        "status": "pending"
    }

    try:
        # API'ga order yuborish
        response = requests.post(ORDERS_API_URL, json=order_data)

        if response.status_code == 201:
            order_id = response.json().get("id")  # Buyurtma ID ni olish

            # Foydalanuvchiga tasdiq xabari
            await call.message.edit_text(
                f"✅ Buyurtma yaratildi #{order_id}! Haydovchi qidirilmoqda, topilganda sizga xabar beramiz.",
                reply_markup=None
            )

            # ✅ Guruhga buyurtmani yuborish uchun `group.py` dagi funksiyani chaqiramiz
            await send_order_to_group(order_id, order_data)

        else:
            await call.message.edit_text(f"❌ Xatolik yuz berdi: {response.status_code} - {response.text}", reply_markup=None)

    except Exception as e:
        await call.message.edit_text(f"❌ Xatolik yuz berdi: {e}", reply_markup=None)

    # State'ni yakunlash
    await state.finish()
    await call.answer()

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(start_order, commands=["start_order"], state="*")
    dp.register_message_handler(start_order, text="📋 Buyurtma berish", state="*")
    # Yo'nalish tanlash
    dp.register_callback_query_handler(handle_direction_selection,lambda c: c.data in ['toshkent_vodiy', 'vodiy_toshkent'],state=PessengerOrderState.direction)
    
    # Jo'nash joyini tanlash
    dp.register_callback_query_handler(
        handle_pickup_location,
        lambda c: c.data in [
            'namangan', 'farg\'ona', 'andijon',  # Vodiy viloyatlari
            'bektemir', 'chilonzor', 'mirobod', 'mirzo_ulug\'bek', 'olmazor',
            'sergeli', 'shayhontohur', 'uchtepa', 'yakkassaroy', 'yashnaobod', 'yunusobod'  # Toshkent tumanlari
        ],
        state=PessengerOrderState.pickup_location
    )
    
    # Tushish joyini tanlash
    dp.register_callback_query_handler(
        handle_dropoff_location,
        lambda c: c.data in [
            'namangan', 'farg\'ona', 'andijon',  # Vodiy viloyatlari
            'bektemir', 'chilonzor', 'mirobod', 'mirzo_ulug\'bek', 'olmazor',
            'sergeli', 'shayhontohur', 'uchtepa', 'yakkassaroy', 'yashnaobod', 'yunusobod'  # Toshkent tumanlari
        ],
        state=PessengerOrderState.dropoff_location
    )
    
    # Ketish vaqtni tanlash
    dp.register_callback_query_handler(
        handle_pickup_time,
        lambda c: c.data in ['08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00', '22:00', '23:00' ],
        state=PessengerOrderState.departure_time
    )

    # Yo'lovchilar soni tanlash
    dp.register_callback_query_handler(
        handle_passenger_count,
        lambda c: c.data in ['1', '2', '3', '4'],
        state=PessengerOrderState.passenger_count
    )

    # Buyurtmani tasdiqlash yoki bekor qilish
    dp.register_callback_query_handler(
        handle_confirm_order,
        lambda c: c.data in ['confirm_order', 'cancel_order'],
        state=PessengerOrderState.confirm_order
    )
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from utils.keyboards import direction_keyboard, vodiy_region_keyboard, tashkent_region_keyboard, departure_time_keyboard
import requests
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config_data import API_URL, ORDERS_API_URL
from .group_order import send_order_to_group

class ShipperOrderState(StatesGroup):
    direction = State()
    pickup_location = State()
    dropoff_location = State()
    departure_time = State()
    confirm_order = State()

# Buyurtma jarayonini boshlash
async def start_order(message: types.Message):
    await message.answer("Yo'nalishni tanlang", reply_markup=direction_keyboard())
    await ShipperOrderState.direction.set()

async def handle_direction_selection(call: types.CallbackQuery, state: FSMContext):
    direction = call.data
    await state.update_data(direction=direction)

    if direction == 'toshkent_vodiy':
        await call.message.edit_text("📍 Toshkentning qaysi tumanidasiz hozir?", reply_markup=tashkent_region_keyboard())
    elif direction == 'vodiy_toshkent':
        await call.message.edit_text("📍 Vodiyning qaysi viloyatidasiz hozir?", reply_markup=vodiy_region_keyboard())

    await ShipperOrderState.pickup_location.set()
    await call.answer()

# Jo'nash joyini tanlashni qayta ishlash
async def handle_pickup_location(call: types.CallbackQuery, state: FSMContext):
    pickup_location = call.data
    await state.update_data(pickup_location=pickup_location)

    data = await state.get_data()
    direction = data.get('direction')

    if direction == 'toshkent_vodiy':
        await call.message.edit_text("📍 Vodiyning qaysi viloyatiga yuk yuborasiz?:", reply_markup=vodiy_region_keyboard())
    elif direction == 'vodiy_toshkent':
        await call.message.edit_text("📍 Toshkentning qaysi tumaniga yuk yuborasiz?:", reply_markup=tashkent_region_keyboard())

    await ShipperOrderState.dropoff_location.set()
    await call.answer()

# Tushish joyini tanlashni qayta ishlash
async def handle_dropoff_location(call: types.CallbackQuery, state: FSMContext):
    dropoff_location = call.data
    await state.update_data(dropoff_location=dropoff_location)

    await call.message.edit_text("📅 Yuborish vaqtni tanlang:", reply_markup=departure_time_keyboard())
    await ShipperOrderState.departure_time.set()
    await call.answer()

async def handle_pickup_time(call: types.CallbackQuery, state: FSMContext):
    departure_time = call.data  # pickup_time olish
    await state.update_data(departure_time=departure_time)


    # Foydalanuvchi ma'lumotlari
    data = await state.get_data()
    direction = data.get('direction')
    pickup_location = data.get('pickup_location')
    dropoff_location = data.get('dropoff_location')
    departure_time = data.get('departure_time')

    # Buyurtma ma'lumotlarini tekshirish
    await call.message.edit_text(
        f"✅ Buyurtma ma'lumotlari:\n\n"
        f"↔️ Yo'nalish: {direction.title()}\n"
        f"📍 Yukni olib ketish joyi: {pickup_location.title()}dan - {dropoff_location.title()}ga\n"
        f"📅 Yukni olib ketish vaqti: {departure_time}\n"
        f"❓ Buyurtmani tasdiqlaysizmi?",
        reply_markup=InlineKeyboardMarkup(row_width=2).add(
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_order"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_order")
        )
    )

    await ShipperOrderState.confirm_order.set()
    await call.answer()


async def handle_confirm_order(call: types.CallbackQuery, state: FSMContext):
    shipper = call.from_user.id

    try:
        # API'dan shipper ma'lumotlarini olish
        get_shipper_id = requests.get(API_URL + f"user/{shipper}/")
        get_shipper_id.raise_for_status()
        shipper_id = get_shipper_id.json().get('id')
        if not shipper_id:
            raise ValueError("Yuk yuboruvchining ID raqami topilmadi")
        print(f"Yuk yuboruvchi ID: {shipper_id} ******")

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
        "order_type": "shipper",
        "shipper": shipper_id,
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
    dp.register_message_handler(start_order, commands=["start_ship_order"], state="*")
    dp.register_message_handler(start_order, text="📦 Yuk yuborish", state="*")
    # Yo'nalish tanlash
    dp.register_callback_query_handler(handle_direction_selection,lambda c: c.data in ['toshkent_vodiy', 'vodiy_toshkent'],state=ShipperOrderState.direction)
    
    # Jo'nash joyini tanlash
    dp.register_callback_query_handler(
        handle_pickup_location,
        lambda c: c.data in [
            'namangan', 'farg\'ona', 'andijon',  # Vodiy viloyatlari
            'bektemir', 'chilonzor', 'mirobod', 'mirzo_ulug\'bek', 'olmazor',
            'sergeli', 'shayhontohur', 'uchtepa', 'yakkassaroy', 'yashnaobod', 'yunusobod'  # Toshkent tumanlari
        ],
        state=ShipperOrderState.pickup_location
    )
    
    # Tushish joyini tanlash
    dp.register_callback_query_handler(
        handle_dropoff_location,
        lambda c: c.data in [
            'namangan', 'farg\'ona', 'andijon',  # Vodiy viloyatlari
            'bektemir', 'chilonzor', 'mirobod', 'mirzo_ulug\'bek', 'olmazor',
            'sergeli', 'shayhontohur', 'uchtepa', 'yakkassaroy', 'yashnaobod', 'yunusobod'  # Toshkent tumanlari
        ],
        state=ShipperOrderState.dropoff_location
    )
    
    # Ketish vaqtni tanlash
    dp.register_callback_query_handler(
        handle_pickup_time,
        lambda c: c.data in ['08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00', '22:00', '23:00' ],
        state=ShipperOrderState.departure_time
    )

    # Buyurtmani tasdiqlash yoki bekor qilish
    dp.register_callback_query_handler(
        handle_confirm_order,
        lambda c: c.data in ['confirm_order', 'cancel_order'],
        state=ShipperOrderState.confirm_order
    )
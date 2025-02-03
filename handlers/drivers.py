from aiogram import types, Dispatcher
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from utils.keyboards import direction_keyboard, tashkent_region_keyboard, vodiy_region_keyboard
import requests
from config_data import API_URL, USERS_API_URL, UPDATE_ROLE_USER_API_URL

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
        await call.answer()

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(start_location_driver, commands=['location_driver'])
    dp.register_message_handler(start_location_driver, text="📍 Yurish joyi tanlash", state="*")
    dp.register_callback_query_handler(handle_current_direction, state=DriverLocationState.current_direction)
    dp.register_callback_query_handler(handle_current_region, state=DriverLocationState.current_region)
    dp.register_callback_query_handler(handle_dropoff_location, state=DriverLocationState.dropoff_location)
from aiogram import types, Dispatcher
from aiogram.utils.markdown import escape_md
from config_data import API_URL, ORDERS_FILTER_API
import requests
from utils.keyboards import passenger_keyboard


async def get_all_orders(message: types.Message):
    passenger = message.from_user.id
    print(f"Passenger Telegram ID: {passenger}")

    try:
        # Passenger ID ni olish
        get_passenger_id = requests.get(API_URL + f"user/{passenger}/")
        get_passenger_id.raise_for_status()  # HTTP xatoliklarni tekshirish
        passenger_id = get_passenger_id.json().get('id')  # .get() xavfsizroq

        # Buyurtmalarni olish
        get_all_orders_url = f"{API_URL}user/{passenger_id}/orders/"
        response = requests.get(get_all_orders_url)
        response.raise_for_status()  # HTTP xatoliklarni tekshirish
        orders = response.json()

    except requests.exceptions.RequestException as e:
        await message.answer(f"❌ API bilan bog'lanishda xatolik yuz berdi: {str(e)}", reply_markup=None)
        return
    
    except ValueError as e:
        await message.answer(f"❌ {str(e)}", reply_markup=None)
        return

    # Agar buyurtmalar mavjud bo'lmasa
    if not orders:
        await message.answer("Sizning buyurtmangiz mavjud emas!", reply_markup=None)
        return

    # Buyurtmalarni formatlash va yuborish
    for order in orders:
        order_type = "Yo'lovchi" if order['order_type'] == 'passenger' else "Yuk yuboruvchi"
        order_text = (
            f"📋 *Buyurtma ID:* {escape_md(order['id'])}\n\n"
            f"📑 *Buyurtma turi:* {escape_md(order_type)}\n"
            f"🚖 *Yo'nalish:* {escape_md(order['direction'])}\n"
            f"📍 *Manzil:* {escape_md(order['pickup_location']).title()} → {escape_md(order['dropoff_location']).title()}\n"
            f"🕒 *Vaqt:* {escape_md(order['departure_time'])}\n"
            f"📋 *Holat:* {escape_md(order['status'])}\n"
        )
        if order['order_type'] == 'passenger':
            order_text += f"👥 *Yo'lovchilar soni:* {escape_md(order['passenger_count'])}\n"

        await message.answer(order_text, parse_mode='Markdown')




def register_handlers(dp: Dispatcher):
    dp.register_message_handler(get_all_orders, commands=["get_all_orders"], state="*")
    dp.register_message_handler(get_all_orders, text="📋 Barcha Buyurtmalar", state="*")
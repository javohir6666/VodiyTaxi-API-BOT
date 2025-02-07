import requests
from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# API URL larini aniqlash
from config_data import API_URL, GROUP_ID, ORDER_UPDATE_API, GET_DRIVER_API, GET_PASSENGER_API, GET_SHIPPER_API


def get_user_info(driver_id):
    """ Haydovchi ma'lumotlarini API orqali olish """
    response = requests.get(f"{API_URL}user/{driver_id}/")
    if response.status_code == 200:
        return response.json()
    return None

def get_driver_info(user_id):
    """ Haydovchi ma'lumotlarini API orqali olish """
    response = requests.get(f"{GET_DRIVER_API}{user_id}/")
    if response.status_code == 200:
        return response.json()
    return None


def get_passenger_info(user_id):
    """ Buyurtmachi ma'lumotlarini API orqali olish """
    response = requests.get(f"{GET_PASSENGER_API}{user_id}/")
    if response.status_code == 200:
        return response.json()
    return None

def get_shipper_info(user_id):
    """ Buyurtmachi ma'lumotlarini API orqali olish """
    response = requests.get(f"{GET_SHIPPER_API}{user_id}/")
    if response.status_code == 200:
        return response.json()
    return None


async def send_order_to_group(order_id, order_data):
    """ Buyurtmani guruhga yuborish """
    order_type = order_data['order_type']
    if order_type == 'passenger':
        order_type = 'Yo\'lovchi'
    elif order_type == 'shipper':
        order_type = 'Yuk yuboruvchi'
    order_text = (
        f"🆕 Yangi buyurtma!\n"
        f"📑 Buyurtma turi: {order_type}\n"
        f"🚖 Yo'nalish: {order_data['direction']}\n"
        f"📍 Manzil: {order_data['pickup_location'].title()} → {order_data['dropoff_location']}\n"
        f"🕒 Vaqt: {order_data['departure_time']}\n"
    )

    if order_type == 'passenger':
        order_text += f"👥 Yo'lovchilar soni: {order_data['passenger_count']}\n"

    # Tasdiqlash tugmasi
    keyboard = InlineKeyboardMarkup()
    confirm_button = InlineKeyboardButton("✅ Qabul qilish", callback_data=f"accept_{order_id}")
    keyboard.add(confirm_button)
    from bot import bot
    await bot.send_message(GROUP_ID, order_text, reply_markup=keyboard)


async def handle_driver_accept_order(call: types.CallbackQuery):
    if not call.data.startswith("accept_"):
        return  # Noto'g'ri callback bo‘lsa, qaytib ketamiz
    """ Haydovchi buyurtmani qabul qilganda ishlaydi """
    driver_id = call.from_user.id
    get_driver = get_user_info(driver_id)
    driver = get_driver.get('id')
    order_id = call.data.split("_")[1]
    print(f"Haydovchi qabul qilyapti ID:{driver}")
    # API orqali buyurtmani yangilash
    update_data = {"driver": driver, "status": "accepted"}
    
    response = requests.patch(f"{ORDER_UPDATE_API}{order_id}/", json=update_data)
    order = response.json()

        
    message = (
            f"✅ #{order_id}-sonli buyurtma {get_driver['telegram_fullname']} tomonidan qabul qilindi! \n"
            f"👤 Mijoz ma'lumotlari shaxsiy xabardan yuborildi haydovchiga!"
            )

    if response.status_code == 200:
        await call.message.edit_text(message, reply_markup=None)

        # Yo‘lovchiga haydovchi haqida ma’lumot yuborish
        order_info = response.json()
        await notify_driver_about_passenger(driver_id,order_info)
        await notify_passenger_about_driver(driver_id, order_info)
    else:
        await call.answer("❌ Xatolik yuz berdi, iltimos qayta urinib ko'ring.", show_alert=True)

async def notify_driver_about_passenger(driver_id,order_info):
    order_type = order_info['order_type']
    order_id = order_info['id']

    if order_type == 'passenger':
    # Passenger ma'lumotlarini olish
        passenger_id = order_info['passenger']
        user_passenger_info = get_passenger_info(passenger_id)
        passenger_phone = user_passenger_info['user']['phone_number']
        
        message = (
                f"✅ #{order_id}-sonli buyurtmangiz! \n\n"
                f"🚖 Yo'nalish: {order_info['direction'].title()}\n"
                f"📍 Manzil: {order_info['pickup_location'].title()} → {order_info['dropoff_location'].title()}\n"
                f"🕒 Ketish Vaqti: {order_info['departure_time'].title()}\n"   
                f"📞 Mijoz Telefoni: {passenger_phone}"
                )
    else:
        # Yuk yuboruvchining ma'lumotlarini olish
        shipper_id = order_info['shipper']
        user_shipper_info = get_shipper_info(shipper_id)
        shipper_phone = user_shipper_info['user']['phone_number']
        
        message = (
                f"✅ #{order_id}-sonli buyurtmangiz! \n\n"
                f"🚖 Yo'nalish: {order_info['direction'].title()}\n"
                f"📍 Yukni olib ketish manzili: {order_info['pickup_location'].title()} → {order_info['dropoff_location'].title()}\n"
                f"🕒 Yukni olib ketish vaqti: {order_info['departure_time'].title()}\n"   
                f"📞 Yuk yuboruvchi telefoni: {shipper_phone}"
                )
        keyboard = InlineKeyboardMarkup()
        reject_button = InlineKeyboardButton("❌ Bekor qilish", callback_data=f"cancelorderdriver_{order_info['id']}")
        keyboard.add(reject_button)
        from bot import bot
        await bot.send_message(driver_id, message, reply_markup=keyboard)

async def notify_passenger_about_driver(driver_id, order_info):
    """ Yo‘lovchiga haydovchi haqida xabar berish """
    order_type = order_info['order_type']
    
    driver_info = get_user_info(driver_id)
    user_driver_info = get_driver_info(driver_info.get('id'))

    from bot import bot
    if order_type == 'passenger':
        passenger_id = order_info['passenger']
        user_passenger_info = get_passenger_info(passenger_id)
        passenger = user_passenger_info['user']['telegram_id']
        if driver_info and user_driver_info:
            message = (
                f"🚖 Buyurtmangiz qabul qilindi!\n\n" 
                f"🔢 Buyurtma raqami: #{order_info['id']}\n"
                f"👤 Haydovchi: {driver_info['telegram_fullname']}\n"
                f"🚖 Avtomobil: {user_driver_info['car_name'].title()} | {user_driver_info['car_number']}\n"
                f"📞 Telefon: {driver_info['phone_number']}"
            )
            keyboard = InlineKeyboardMarkup()
            reject_button = InlineKeyboardButton("❌ Bekor qilish", callback_data=f"cancelorderpassenger_{order_info['id']}")
            keyboard.add(reject_button)
            await bot.send_message(passenger, message, reply_markup=keyboard)
        else:
            await bot.send_message(passenger, "❌ Haydovchi ma'lumotlari olinmadi, administrator bilan bog'laning.")
    elif order_type =='shipper':
        
        shipper_id = order_info['shipper']
        user_shipper_info = get_shipper_info(shipper_id)
        shipper = user_shipper_info['user']['telegram_id']
        if driver_info and user_driver_info:
            message = (
                f"🚖 Buyurtmangiz qabul qilindi!\n\n" 
                f"🔢 Buyurtma raqami: #{order_info['id']}\n"
                f"👤 Haydovchi: {driver_info['telegram_fullname']}\n"
                f"🚖 Avtomobil: {user_driver_info['car_name'].title()} | {user_driver_info['car_number']}\n"
                f"📞 Telefon: {driver_info['phone_number']}"
            )
            keyboard = InlineKeyboardMarkup()
            reject_button = InlineKeyboardButton("❌ Bekor qilish", callback_data=f"cancelordershipper_{order_info['id']}")
            keyboard.add(reject_button)
            await bot.send_message(shipper, message, reply_markup=keyboard)
        else:
            await bot.send_message(shipper, "❌ Haydovchi ma'lumotlari olinmadi, administrator bilan bog'laning.")


# Handler'larni ro'yxatdan o'tkazish
def register_group_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(lambda c: c.data.startswith("accept_"), handle_driver_accept_order)

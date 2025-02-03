import aiohttp, re, requests
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from config_data import API_URL

class OrderState(StatesGroup):
    waiting_for_driver_response = State()

async def send_order_to_driver(driver, order):
    """
    Haydovchiga buyurtma yuborish.
    """
    message = (
        f"🚗 Yangi buyurtma! #{order.id}\n\n"
        f"↔️ Yo'nalish: {order.direction}\n"
        f"📍 Manzil: {order.dropoff_location}\n"
        f"👥 Yo'lovchilar soni: {order.passenger_count} ta\n"
        f"⏰ Ketish vaqti: {order.departure_time}\n\n"
        f"❓ Qabul qilasizmi?"
    )

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(
            text="✅ Tasdiqlash", 
            callback_data=f"accept_order_{order.id}_{driver.user.telegram_id}"
        ),
        InlineKeyboardButton(
            text="❌ Bekor qilish", 
            callback_data=f"reject_order_{order.id}_{driver.user.telegram_id}"
        )
    )
    from bot import bot
    await bot.send_message(driver.user.telegram_id, message, reply_markup=keyboard)
    # Yuborilgan xabarga javoban qaytish: True (xabar yuborildi)
    return True

async def get_user_id_by_telegram_id(telegram_id):
    """
    API orqali telegram_id bo‘yicha user_id ni olish.
    """
    url = f"{API_URL}{telegram_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("id")
            else:
                return None

async def handle_driver_order_action(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Haydovchining callback tugmalariga bosishiga mos ravishda buyurtma holatini yangilash va
    yo‘lovchini xabardor qilish.
    """
    from bot import bot
    driver_telegram_id = callback_query.from_user.id
    driver_user_id = await get_user_id_by_telegram_id(driver_telegram_id)
    if not driver_user_id:
        await bot.send_message(driver_telegram_id, "❌ Haydovchi ma'lumotlari topilmadi.")
        await callback_query.answer()
        await state.finish()
        return

    callback_data = callback_query.data  # Masalan: "accept_order_1234_987654321"
    parts = callback_data.split("_")
    if len(parts) < 4:
        await bot.send_message(driver_telegram_id, "❌ Buyurtma ma'lumotlari noto'g'ri.")
        await callback_query.answer()
        await state.finish()
        return

    action = parts[0]  # "accept" yoki "reject"
    try:
        order_id = int(parts[2])
    except ValueError:
        await bot.send_message(driver_telegram_id, "❌ Buyurtma ID noto'g'ri.")
        await callback_query.answer()
        await state.finish()
        return

    # API da buyurtmani yangilash uchun URL
    order_endpoint = f"{API_URL}order/{order_id}/"
    if action == "accept":
        order_data = {
            "driver": driver_user_id,
            "status": "accepted"
        }
    elif action == "reject":
        # Agar buyurtma rad etilsa, uni "pending" deb qoldirib, keyingi haydovchini izlash jarayonini boshlash mumkin
        order_data = {
            "driver": None,
            "status": "pending"
        }
    else:
        await callback_query.answer("❌ Noto'g'ri amal")
        await state.finish()
        return

    async with aiohttp.ClientSession() as session:
        if action == "accept":
            try:
                async with session.post(order_endpoint, json=order_data) as response:
                    if response.status == 200:
                        await callback_query.message.edit_text("✅ Buyurtma qabul qilindi!", reply_markup=None)
                    else:
                        error_text = await response.text()
                        await bot.send_message(driver_telegram_id, f"❌ Buyurtma qabul qilinmadi. Xatolik: {error_text}")
                        await callback_query.answer()
                        await state.finish()
                        return
            except Exception as e:
                await bot.send_message(driver_telegram_id, f"❌ Buyurtma qabul qilinmadi. Xatolik: {str(e)}")
                await callback_query.answer()
                await state.finish()
                return

            # Yo‘lovchiga xabar yuborish
            try:
                async with session.get(order_endpoint) as response:
                    if response.status == 200:
                        order = await response.json()
                        passenger = order.get("passenger", {})
                        passenger_telegram_id = passenger.get("user", {}).get("telegram_id")
                        if passenger_telegram_id:
                            message = (
                                "✅ Buyurtmangiz qabul qilindi! 🚖\n\n"
                                "Haydovchi siz bilan bog‘lanadi."
                            )
                            await bot.send_message(passenger_telegram_id, message)
                        else:
                            await bot.send_message(driver_telegram_id, "❌ Yo‘lovchining Telegram ID si topilmadi.")
                    else:
                        await bot.send_message(driver_telegram_id, "❌ Buyurtma ma'lumotlari olinmadi.")
            except Exception as e:
                await bot.send_message(driver_telegram_id, f"❌ Xatolik: {str(e)}")
        elif action == "reject":
            await callback_query.message.edit_text("❌ Buyurtma rad etildi!", reply_markup=None)
            # Rad etilgan buyurtma holati “pending” qoldirilib, signals.py dagi jarayon orqali keyingi haydovchi izlanishi mumkin.
    await callback_query.answer()
    await state.finish()

def register_handler(dp: Dispatcher):
    """
    Callback query handlerini ro'yxatdan o'tkazish.
    """
    dp.register_callback_query_handler(
        handle_driver_order_action,
        lambda c: c.data and (c.data.startswith("accept_order") or c.data.startswith("reject_order")),
        state=OrderState.waiting_for_driver_response
    )
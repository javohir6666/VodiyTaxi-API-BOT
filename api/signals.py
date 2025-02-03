import threading
import asyncio
import logging
import aiohttp
from asgiref.sync import sync_to_async
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order, Driver

from handlers.driver_order import send_order_to_driver
from config_data import ORDER_DETAIL_API

@receiver(post_save, sender=Order)
def process_order(sender, instance, created, **kwargs):
    """
    Yangi buyurtma yaratilganda asinxron ravishda haydovchini qidirish va xabar yuborish jarayonini boshlash.
    """
    if created:
        threading.Thread(target=asyncio.run, args=(find_and_notify_driver(instance),)).start()

@sync_to_async
def get_potential_drivers(order):
    """
    Buyurtmaga mos keladigan haydovchilarni sinxron ORM so‘rovi yordamida qaytarish.
    """
    return list(Driver.objects.filter(
        current_direction=order.direction,
        dropoff_location=order.dropoff_location,
        seats_available__gte=order.passenger_count
    ))

@sync_to_async
def save_order(order):
    """
    Buyurtma obyektini asinxron muhitda saqlash.
    """
    order.save()

@sync_to_async
def get_driver_user(driver):
    """
    Haydovchi bilan bog‘liq foydalanuvchi obyektini qaytarish.
    """
    return driver.user

async def find_and_notify_driver(order):
    """
    Buyurtmaga mos haydovchini topish va unga Telegram orqali xabar yuborish.
    Javob kelishi uchun belgilangan vaqt davomida kuzatib boriladi.
    """
    logging.info(f"🔍 Haydovchilar qidirilmoqda. Order ID: {order.id}, Yo'nalish: {order.direction}")
    potential_drivers = await get_potential_drivers(order)
    logging.info(f"🚗 {len(potential_drivers)} ta haydovchi topildi")

    for driver in potential_drivers:
        user = await get_driver_user(driver)
        logging.info(f"📨 {user.telegram_fullname} ga buyurtma yuborilmoqda...")
        await send_order_to_driver(driver, order)

        # Buyurtma uchun haydovchining javobini kutamiz (masalan, 30 soniya)
        response_status = await wait_for_driver_response(order.id, timeout=30)
        if response_status == "accepted":
            logging.info(f"✅ {user.telegram_fullname} buyurtmani qabul qildi!")
            order.driver = driver
            order.status = "accepted"
            await save_order(order)
            await notify_passenger(order)
            return
        elif response_status == "rejected":
            logging.info(f"❌ {user.telegram_fullname} buyurtmani rad etdi!")
            # Keyingi haydovchiga o'tish
            continue

    logging.info("❌ Hech bir haydovchi buyurtmani qabul qilmadi.")
    order.status = "no_driver"
    await save_order(order)

async def wait_for_driver_response(order_id, timeout=30):
    """
    API orqali buyurtma statusini polling usulida kuzatib boramiz.
    Agar haydovchi javobi ("accepted" yoki "rejected") kelmasa, timeout tugagach None qaytariladi.
    """
    order_endpoint = f"{ORDER_DETAIL_API}{order_id}/"
    elapsed = 0
    interval = 5
    async with aiohttp.ClientSession() as session:
        while elapsed < timeout:
            async with session.get(order_endpoint) as response:
                if response.status == 200:
                    order_data = await response.json()
                    status = order_data.get("status")
                    if status in ["accepted", "rejected"]:
                        return status
            await asyncio.sleep(interval)
            elapsed += interval
    return None

async def notify_passenger(order):
    """
    Yo‘lovchiga buyurtma qabul qilinishi haqida xabar yuborish.
    """
    order_endpoint = f"{ORDER_DETAIL_API}{order.id}/"
    async with aiohttp.ClientSession() as session:
        async with session.get(order_endpoint) as response:
            if response.status == 200:
                order_data = await response.json()
                passenger = order_data.get("passenger", {})
                passenger_telegram_id = passenger.get("user", {}).get("telegram_id")
                if passenger_telegram_id:
                    message = (
                        "✅ Buyurtmangiz qabul qilindi! 🚖\n\n"
                        "Haydovchi siz bilan bog‘lanadi."
                    )
                    from bot import bot
                    await bot.send_message(passenger_telegram_id, message)
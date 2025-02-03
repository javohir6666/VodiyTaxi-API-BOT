from aiogram import types
from aiogram.types import ParseMode
from .register import start_registration
from config_data import API_URL
from utils.keyboards import passenger_keyboard, driver_keyboard,shipper_keyboard
import requests

async def start(message: types.Message):
    telegram_id = message.from_user.id
    
    response = requests.get(f"{API_URL}user/{telegram_id}/")  

    if response.status_code == 200:
        data = response.json()
        print("Response JSON:", data)  # JSON ma'lumotlarni ko'rish uchun

        if isinstance(data, dict):
            print("JSON keys:", data.keys())  # JSON kalitlarini chiqaramiz

            is_registered = data.get("is_registered", False)  # Tavsiya etilgan usul
            role = data.get("active_role")
            if is_registered:
                if role == "passenger":
                    await message.answer("Xush kelibsiz yo'lovchi!", reply_markup=passenger_keyboard())
                elif role == "driver":
                    await message.answer("Xush kelibsiz haydovchi!", reply_markup=driver_keyboard())
                elif role == "shipper":
                    await message.answer("Xush kelibsiz yuk yuboruvchi!", reply_markup=shipper_keyboard())
            else:
                await start_registration(message)
        else:
            await start_registration(message)
    elif response.status_code == 404:
        await start_registration(message)
    else:
        await message.answer("Xato yuz berdi, iltimos qaytadan urinib ko'ring.")


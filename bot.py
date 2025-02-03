import logging
from aiogram import Bot, Dispatcher
from aiogram.types import ParseMode
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from handlers.start import start
from handlers import register, passenger_order, passengers, drivers, driver_order, group_order, shipper_order
from config_data import API_TOKEN
from aiogram.contrib.fsm_storage.memory import MemoryStorage



logging.basicConfig(level=logging.INFO)

storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)

dp.middleware.setup(LoggingMiddleware())

# Start komandasi
dp.register_message_handler(start, commands="start")
register.register_handlers(dp)
passenger_order.register_handlers(dp)
passengers.register_handlers(dp)
drivers.register_handlers(dp)
driver_order.register_handler(dp)
group_order.register_group_handlers(dp)
shipper_order.register_handlers(dp)
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

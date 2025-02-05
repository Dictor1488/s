from aiogram import executor

import modules
import time
from loader import vip
from colorama import Fore, Style


author = Fore.LIGHTRED_EX + Style.BRIGHT + "Made By " + Fore.LIGHTGREEN_EX + Style.BRIGHT + "@business_dark" + Fore.RESET + Style.NORMAL + '\n'
start = Fore.LIGHTYELLOW_EX + Style.BRIGHT + "Бот успешно запущен!" + Fore.RESET + Style.NORMAL + '\n'

if __name__ == '__main__':
    time.sleep(0.03)
    print(author, end='', flush=True)
    time.sleep(0.03)
    print(start, end='', flush=True)
    executor.start_polling(vip)

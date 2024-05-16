import asyncio
import time
import datetime
from os import system
from random import randint
import traceback

from telethon.sync import TelegramClient, errors, events
from telethon.custom import Dialog, Message
from telethon.tl.functions.messages import GetDialogFiltersRequest
import schedule

from bot_utils import print_with_time, append_to_file, add_time_prefix
from settings import Settings

ERROR_FILE_NAME = 'errors.txt'
class Bot:
  def __init__(self, settings: Settings, client: TelegramClient):
    self.__settings = settings
    self.__client = client
    self.__timeouts_dialogs = {}
    self.__bad_request_errors_count = 0
    self.__success_send_messages_count = 0
    self.__has_premium = False
    self.__last_saved_message: Message = None

    self.__allow_mailing = True
    self.__start_schedule = None
    self.__end_schedule = None

    if settings.has('schedule') and settings.get('schedule'):
      self.__allow_mailing = False
      self.__init_schedule()

    self.__client.add_event_handler(self.__last_saved_message_handler, events.NewMessage(outgoing=True, chats='me'))
    self.__client.add_event_handler(self.__modify_last_saved_message_handler, events.MessageEdited(outgoing=True, chats='me'))

  def __init_schedule(self):
    start_hour = self.__settings.get('schedule_start_hour')
    end_hour = self.__settings.get('schedule_end_hour')

    current_time = datetime.datetime.now().time()
    start_time = datetime.time(start_hour)
    end_time = datetime.time(end_hour)

    if start_time <= end_time and start_time <= current_time < end_time:
      self.__allow_mailing = True
    elif start_time > end_time and (start_time <= current_time or current_time < end_time):
      self.__allow_mailing = True

    self.__start_schedule = schedule.every().day.at(f"{start_hour if start_hour > 9 else '0' + str(start_hour)}:00").do(self.__toggle_mailing, True)
    self.__end_schedule = schedule.every().day.at(f"{end_hour if end_hour > 9 else '0' + str(end_hour)}:00").do(self.__toggle_mailing, False)

  def __toggle_mailing(self, value):
    self.__allow_mailing = value

  async def __wait_allow_mailing(self):
    while not self.__allow_mailing:
      schedule.run_pending()
      await asyncio.sleep(5)

  async def __get_dialogs(self):
    dialogs = []

    dialog: Dialog
    async for dialog in self.__client.iter_dialogs(ignore_migrated=True):
      if dialog.is_group:
        if settings.get('process_only_unread_dialogs') and dialog.unread_count < settings.get('dialog_unread_count'):
          continue

        dialogs.append(dialog)

    return dialogs
  
  async def __get_last_saved_message(self) -> Message:
    async for message in self.__client.iter_messages('me', 1):
      return message
    
  def __set_dialog_timeout(self, dialog_id, timeout_sec):
    self.__timeouts_dialogs[dialog_id] = time.time() + timeout_sec

  def __remove_dialog_timeout(self, dialog_id):
    if dialog_id in self.__timeouts_dialogs:
      del self.__timeouts_dialogs[dialog_id]

  def __is_dialog_timeout(self, dialog_id):
    if dialog_id in self.__timeouts_dialogs:
      if time.time() > self.__timeouts_dialogs[dialog_id]:
        return True
      else:
        self.__remove_dialog_timeout(dialog_id)
    return False
  
  async def __last_saved_message_handler(self, event):
    print("Прийшло нове повідомлення для відправлення!")
    self.__last_saved_message = event.message

  async def __modify_last_saved_message_handler(self, event):
    print("Повідомлення для відправлення оновлено!")
    if not self.__last_saved_message:
      return
    
    if self.__last_saved_message.id == event.message.id:
      self.__last_saved_message = event.message

  async def __mailing_cycle(self, dialogs):
    success_send_count = 0

    dialog: Dialog
    for dialog in dialogs:
      if self.__is_dialog_timeout(dialog.id):
        continue

      try:
        if self.__has_premium:
          await self.__client.send_message(dialog, message=self.__last_saved_message)
        else:
          await self.__client.send_message(dialog, self.__last_saved_message.text, parse_mode='md')

        # print_with_time(f'Повідомлення відправлено до "{dialog.name}"')

        success_send_count += 1
        self.__bad_request_errors_count = 0
      except errors.ForbiddenError as forbidden_error:
        append_to_file(ERROR_FILE_NAME, add_time_prefix("ForbiddenError"))
        append_to_file(ERROR_FILE_NAME, add_time_prefix(type(forbidden_error)))
        append_to_file(ERROR_FILE_NAME, add_time_prefix(type(forbidden_error).__name__))
        append_to_file(ERROR_FILE_NAME, add_time_prefix(forbidden_error.code))
        append_to_file(ERROR_FILE_NAME, add_time_prefix(forbidden_error.message))
        append_to_file(ERROR_FILE_NAME, add_time_prefix(forbidden_error.__str__() + '\n'))

        try:
          await self.__client.delete_dialog(dialog)
        except:
          pass

        self.__remove_dialog_timeout(dialog.id)

        if dialog.entity.username != None:
          print_with_time(f'Error: {forbidden_error.message} Аккаунт вийшов з @{dialog.entity.username}')
        else:
          print_with_time(f'Error: {forbidden_error.message} Аккаунт вийшов з {dialog.name}')

        self.__bad_request_errors_count = 0

      except errors.SlowModeWaitError as slow_mode_error:
        append_to_file(ERROR_FILE_NAME, add_time_prefix("SlowModeWaitError"))
        append_to_file(ERROR_FILE_NAME, add_time_prefix(type(slow_mode_error)))
        append_to_file(ERROR_FILE_NAME, add_time_prefix(type(slow_mode_error).__name__))
        append_to_file(ERROR_FILE_NAME, add_time_prefix(slow_mode_error.code))
        append_to_file(ERROR_FILE_NAME, add_time_prefix(slow_mode_error.message))
        append_to_file(ERROR_FILE_NAME, add_time_prefix(slow_mode_error.__str__() + '\n'))

        print_with_time(f'Error: {slow_mode_error.message} Потрібне очікування {slow_mode_error.seconds} секунд!')
        print_with_time(f'Діалог "{dialog.name}" буде пропущений на {slow_mode_error.seconds} секунд!')

        self.__set_dialog_timeout(dialog.id, slow_mode_error.seconds)

        self.__bad_request_errors_count = 0

      except errors.FloodWaitError as flood_error:
        append_to_file(ERROR_FILE_NAME, add_time_prefix("FloodWaitError"))
        append_to_file(ERROR_FILE_NAME, add_time_prefix(type(flood_error)))
        append_to_file(ERROR_FILE_NAME, add_time_prefix(type(flood_error).__name__))
        append_to_file(ERROR_FILE_NAME, add_time_prefix(flood_error.code))
        append_to_file(ERROR_FILE_NAME, add_time_prefix(flood_error.message))
        append_to_file(ERROR_FILE_NAME, add_time_prefix(flood_error.__str__() + '\n'))

        print_with_time(f'Error: {flood_error.message} Потрібне очікування {flood_error.seconds} секунд!')
        await asyncio.sleep(flood_error.seconds + 5)

        self.__bad_request_errors_count = 0

      except errors.BadRequestError as bad_request_error:
        append_to_file(ERROR_FILE_NAME, add_time_prefix("BadRequestError"))
        append_to_file(ERROR_FILE_NAME, add_time_prefix(type(bad_request_error)))
        append_to_file(ERROR_FILE_NAME, add_time_prefix(type(bad_request_error).__name__))
        append_to_file(ERROR_FILE_NAME, add_time_prefix(bad_request_error.code))
        append_to_file(ERROR_FILE_NAME, add_time_prefix(bad_request_error.message))
        append_to_file(ERROR_FILE_NAME, add_time_prefix(bad_request_error.__str__() + '\n'))

        if bad_request_error.message == 'TOPIC_CLOSED':
          await self.__client.delete_dialog(dialog)
          print_with_time(f'Error: {bad_request_error.message} Діалог "{dialog.name}" закритий!')
          if dialog.entity.username != None:
            print_with_time(f'Error: {forbidden_error.message} Аккаунт вийшов з @{dialog.entity.username}')
          else:
            print_with_time(f'Error: {forbidden_error.message} Аккаунт вийшов з {dialog.name}')

        else:
          self.__bad_request_errors_count += 1
          if self.__bad_request_errors_count >= 3:
            print_with_time(f'Error: {bad_request_error.message} Перевищено максимальну кількість помилок!')
            answ = input(f'Ви бажаєте продовжити процес роботи? (y/n): ')
            if answ.lower() == 'y':
              self.__bad_request_errors_count = 0
            else:
              return False

      except errors.RPCError as rpc_error:
        append_to_file(ERROR_FILE_NAME, add_time_prefix("RPCError"))
        append_to_file(ERROR_FILE_NAME, add_time_prefix(type(rpc_error)))
        append_to_file(ERROR_FILE_NAME, add_time_prefix(type(rpc_error).__name__))
        append_to_file(ERROR_FILE_NAME, add_time_prefix(rpc_error.code))
        append_to_file(ERROR_FILE_NAME, add_time_prefix(rpc_error.message))
        append_to_file(ERROR_FILE_NAME, add_time_prefix(rpc_error.__str__() + '\n'))

        print_with_time(f'Error: {rpc_error.message}')

        self.__bad_request_errors_count = 0

      except Exception as e:
        append_to_file(ERROR_FILE_NAME, add_time_prefix("Exception"))
        append_to_file(ERROR_FILE_NAME, add_time_prefix(type(e)))
        append_to_file(ERROR_FILE_NAME, add_time_prefix(type(e).__name__))
        append_to_file(ERROR_FILE_NAME, add_time_prefix(e))
        append_to_file(ERROR_FILE_NAME, add_time_prefix(traceback.format_exc() + '\n'))

        print_with_time(f'Error: {e}')

        self.__bad_request_errors_count = 0

      finally:
        if self.__settings.has('interval_between_messages'):
          rand_delay = randint(self.__settings.get('min_interval_between_messages'), self.__settings.get('max_interval_between_messages'))
          # print_with_time(f'Очікування між повідомленнями: {rand_delay} секунд')
          await asyncio.sleep(rand_delay)
    
    self.__success_send_messages_count += success_send_count
    return True
    
  
  async def start(self):
    if not self.__allow_mailing:
      print_with_time(f"Розсилка буде запущена в {self.__start_schedule.next_run.strftime('%Y-%m-%d %H:%M:%S')}")
      await self.__wait_allow_mailing()

    all_chats = await self.__get_dialogs()
    self.__last_saved_message = await self.__get_last_saved_message()

    chat_count_limit = self.__settings.has('message_limit_per_cycle') and self.__settings.get('message_limit_per_cycle') or len(all_chats)
    processed_chat_count = 0

    print_cycle_count = 0

    me_info = await self.__client.get_me()
    self.__has_premium = me_info.premium

    print_with_time(f"Premium: {self.__has_premium}")

    await asyncio.sleep(3)

    print_with_time(f"Чатів для розсилки: {len(all_chats)}")

    while True:
      print_cycle_count += 1
      dialogs_for_cycle = all_chats[processed_chat_count : processed_chat_count + chat_count_limit]

      try:
        if not await self.__mailing_cycle(dialogs_for_cycle):
          print_with_time("Зупинено!")
          break
      except Exception as e:
        append_to_file(ERROR_FILE_NAME, add_time_prefix("Exception (while cycle)"))
        append_to_file(ERROR_FILE_NAME, add_time_prefix(type(e)))
        append_to_file(ERROR_FILE_NAME, add_time_prefix(type(e).__name__))
        append_to_file(ERROR_FILE_NAME, add_time_prefix(e.__str__()))
        append_to_file(ERROR_FILE_NAME, add_time_prefix(traceback.format_exc() + '\n'))

        print_with_time(f'Error: {e}')
        break

      schedule.run_pending()

      processed_chat_count += chat_count_limit

      print_with_time('Усього надіслано повідомлень: ', self.__success_send_messages_count)
      print_with_time(f'Оброблено діалогів: {processed_chat_count} / {len(all_chats)}')
      print_with_time('------------------------------')

      if self.__settings.has('break_between_cycle'):
        rand_delay = randint(self.__settings.get('min_break_between_cycle'), self.__settings.get('max_break_between_cycle'))
        print_with_time(f'Очікування між циклами: {rand_delay} секунд')
        await asyncio.sleep(rand_delay)
      elif self.__settings.has('break_between_all_messages'):
        rand_delay = randint(self.__settings.get('min_between_all_messages'), self.__settings.get('max_between_all_messages'))
        print_with_time(f'Очікування між циклами: {rand_delay} секунд')
        await asyncio.sleep(rand_delay)

      if print_cycle_count == 2:
        print_cycle_count = 0
        system('cls')

      if processed_chat_count >= len(all_chats):
        processed_chat_count = 0

        if not self.__allow_mailing:
          print_with_time(f"Розсилку призупинено! Час початку розсилки: {self.__start_schedule.next_run.strftime('%Y-%m-%d %H:%M:%S')}")
          await self.__wait_allow_mailing()

        all_chats = await self.__get_dialogs()
        print_with_time(f"Чатів для розсилки: {len(all_chats)}")
        await asyncio.sleep(10)

      


if __name__ == '__main__':

  settings = Settings()
  settings.init_delays()

  system('cls')

  print_with_time('Ваші налаштування:')
  print_with_time('API_ID:', settings.get('api_id'))
  print_with_time('API_HASH:', settings.get('api_hash'))
  print_with_time('PHONE:', settings.get('phone'))
  print_with_time('Використовувати проксі:', settings.get('use_proxy') and 'Так' or 'Ні')

  print_with_time('Інтервал між повідомленнями: ', settings.has('interval_between_messages') and f'{settings.get("min_interval_between_messages")} - {settings.get("max_interval_between_messages")}' or 'Немає')
  print_with_time('Ліміт повідомлень за цикл: ', settings.has('message_limit_per_cycle') and settings.get('message_limit_per_cycle') or 'Немає')
  print_with_time('Перерва між циклими: ', settings.has('break_between_cycle') and f'{settings.get("min_break_between_cycle")} - {settings.get("max_break_between_cycle")}' or 'Немає')

  if settings.has('break_between_all_messages'):
    print_with_time('Перерва між всіма повідомленнями: ', f'{settings.get("min_between_all_messages")} - {settings.get("max_between_all_messages")}')

  print_with_time('Кількість непрочитаних повідомлень в діалозі для надсилання: ', settings.has('process_only_unread_dialogs') and settings.get('dialog_unread_count') or 'Немає')
  
  print_with_time('Розклад розсилки: ', settings.get('schedule') and 'Так' or 'Ні')
  if settings.has('schedule') and settings.get('schedule'):
    print_with_time('Час початку розсилки: ', settings.get('schedule_start_hour'))
    print_with_time('Час кінця розсилки: ', settings.get('schedule_end_hour'))

  print_with_time('-----------------------------')

  proxy = None
  if settings.get('use_proxy'):
    proxy = {
      'proxy_type': settings.get('proxy_type'),
      'addr': settings.get('proxy_ip'),
      'port': settings.get('proxy_port'),
      'username': settings.get('proxy_login') or None,
      'password': settings.get('proxy_password') or None
    }

  try:
    client = TelegramClient(f'{settings.get("phone")}_session', settings.get('api_id'), settings.get('api_hash'), device_model="FC513IV", system_lang_code="en", lang_code="en", proxy=proxy)
    client.start(phone=settings.get('phone'))

    bot = Bot(settings, client)

    client.loop.run_until_complete(bot.start())
  except Exception as e:
    append_to_file(ERROR_FILE_NAME, add_time_prefix("Exception (main)"))
    append_to_file(ERROR_FILE_NAME, add_time_prefix(type(e)))
    append_to_file(ERROR_FILE_NAME, add_time_prefix(type(e).__name__))
    append_to_file(ERROR_FILE_NAME, add_time_prefix(e.__str__()))
    append_to_file(ERROR_FILE_NAME, add_time_prefix(traceback.format_exc() + '\n'))

    print_with_time(f'Error: {e}')
  finally:
    input('\nPress Enter to exit...')

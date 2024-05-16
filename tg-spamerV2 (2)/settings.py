import os
import json

class Settings:
  def __init__(self):
    if os.path.exists('settings.json'):
      with open('settings.json') as f:
        self.settings = json.load(f)
    else:
      self.settings = {}
      self.__init_setting()

  def save(self):
    with open('settings.json', 'w') as f:
      json.dump(self.settings, f)

  def get(self, key, default=None):
    return self.settings.get(key, default)
  
  def set(self, key, value):
    self.settings[key] = value

  def has(self, key):
    return key in self.settings

  def __init_setting(self):
    api_id = int(input('api_id: '))
    api_hash = input('api_hash: ')
    phone = input('phone: ')

    self.set('api_id', api_id)
    self.set('api_hash', api_hash)
    self.set('phone', phone)

    use_proxy = input('Використовувати проксі y/n: ')
    if use_proxy.lower() == 'y':
      self.set('use_proxy', True)
      self.set('proxy_type', input('Тип проксі (socks5, socks4, http): '))
      self.set('proxy_ip', input('IP адреса проксі: '))
      self.set('proxy_port', int(input('Порт проксі: ')))

      proxy_login = input('Логін проксі (необов\'язкове): ')
      proxy_password = input('Пароль проксі (необов\'язкове): ')

      self.set('proxy_login', proxy_login)
      self.set('proxy_password', proxy_password)

    else:
      self.set('use_proxy', False)
      self.set('proxy_type', '')
      self.set('proxy_ip', '')
      self.set('proxy_port', 0)
      self.set('proxy_login', '')
      self.set('proxy_password', '')

    self.save()

  def init_delays(self):
    add_interval_between_message = input('Інтервал між повідомленнями y/n: ')
    if add_interval_between_message.lower() == 'y':
      self.set('interval_between_messages', True)
      self.set('min_interval_between_messages', int(input('Мінімальний інтервал між повідомленнями (в секундах): ')))
      self.set('max_interval_between_messages', int(input('Максимальний інтервал між повідомленнями (в секундах): ')))

    add_message_limit_per_cycle = input('Ліміт повідомлень за цикл y/n: ')
    if add_message_limit_per_cycle.lower() == 'y':
      self.set('message_limit_per_cycle', int(input('Вкажіть ліміт повідомлень за цикл: ')))

    add_break_between_cycle = input('Перерва між циклими y/n: ')
    if add_break_between_cycle.lower() == 'y':
      self.set('break_between_cycle', True)
      self.set('min_break_between_cycle', int(input('Мінімальна перерва між циклими (в секундах): ')))
      self.set('max_break_between_cycle', int(input('Максимальна перерва між циклими (в секундах): ')))

    if add_interval_between_message.lower() != 'y' and add_message_limit_per_cycle.lower() != 'y' and add_break_between_cycle.lower() != 'y':
      self.set('break_between_all_messages', True)
      self.set('min_between_all_messages', int(input('Мінімальна перерва між всіма повідомленнями (в секундах): ')))
      self.set('max_between_all_messages', int(input('Максимальна перерва між всіма повідомленнями (в секундах): ')))

    process_only_unread_dialogs = input('Надсилати тільки в непрочитані діалоги y/n: ')
    if process_only_unread_dialogs.lower() == 'y':
      self.set('process_only_unread_dialogs', True)
      self.set('dialog_unread_count', int(input('Вкажіть мінімальну кількість непрочитаних повідомлень: ')))

    add_schedule = input('Додати розклад надсилання повідомлень y/n: ')
    if add_schedule.lower() == 'y':
      self.set('schedule', True)
      self.set('schedule_start_hour', int(input('Вкажіть час початку розкладу (годину, 0-23): ')))
      self.set('schedule_end_hour', int(input('Вкажіть час закінчення розкладу (годину, 0-23): ')))
    
    return True
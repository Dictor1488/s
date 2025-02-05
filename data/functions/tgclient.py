import json
from telethon import TelegramClient
from utils import config

class ClientTG:
    client: TelegramClient
    phone: str

    def __init__(self, phone: str = None):
        session_file_path = f'./session/{phone[1:]}.session'
        self.client = TelegramClient(
            session=session_file_path,
            api_id=config('api_id'),
            api_hash=config('api_hash'),
            device_model="Iphone",
            system_version="6.12.0",
            app_version="10 P (28)")

        if phone is not None:
            self.phone = phone

        self.save_session_to_json(session_file_path)

    def save_session_to_json(self, session_file_path):
        session_data = {
            'app_id': config('api_id'),
            'app_hash': config('api_hash'),
            'device': "Iphone",
            'app_version': "10 P (28)",
            'phone': self.phone,
            'session_file': session_file_path
        }
        json_file_path = session_file_path.replace('.session', '.json')
        with open(json_file_path, 'w') as json_file:
            json.dump(session_data, json_file, indent=4)

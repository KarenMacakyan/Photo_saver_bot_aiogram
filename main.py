import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message
from datetime import datetime
import uuid
import re
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pickle

# Configuration
API_TOKEN = "8092471614:AAFkfDjh6wW2OEmIKZ6JhIg6KCpRJ8JlsdU"
GOOGLE_DRIVE_FOLDER_ID = "1-0vUx6wCEZrGxyACvBzMEISWVRIPvNgN"  # Your Google Drive folder ID
BASE_DIR = "photos"

# Google Drive API scopes
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

class GoogleDriveManager:
    def __init__(self):
        self.service = None
        self.creds = None
    
    def authenticate(self):
        """Authenticate with Google Drive API"""
        # Load existing credentials if available
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)
        
        # If credentials are invalid or don't exist, get new ones
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                # You need to create credentials.json from Google Cloud Console
                if not os.path.exists('credentials.json'):
                    print("Please create credentials.json from Google Cloud Console")
                    return False
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)
        
        self.service = build('drive', 'v3', credentials=self.creds)
        return True
    
    def create_folder_if_not_exists(self, folder_name):
        """Create a folder in Google Drive if it doesn't exist"""
        # Check if folder already exists
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and '{GOOGLE_DRIVE_FOLDER_ID}' in parents and trashed=false"
        results = self.service.files().list(q=query).execute()
        files = results.get('files', [])
        
        if files:
            return files[0]['id']
        
        # Create new folder
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [GOOGLE_DRIVE_FOLDER_ID]
        }
        folder = self.service.files().create(body=folder_metadata, fields='id').execute()
        return folder.get('id')
    
    def upload_file(self, file_path, filename, folder_id):
        """Upload a file to Google Drive"""
        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }
        
        media = MediaFileUpload(file_path, resumable=True)
        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        return file.get('id')

# Initialize Google Drive manager
drive_manager = GoogleDriveManager()

def sanitize_filename(filename):
    """Sanitize filename to be safe for file systems"""
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove extra spaces and dots
    filename = re.sub(r'\s+', ' ', filename).strip()
    filename = re.sub(r'\.+$', '', filename)  # Remove trailing dots
    # Limit length
    if len(filename) > 100:
        filename = filename[:100]
    return filename

@dp.message(F.photo)
async def handle_photo(message: Message):
    """Handle incoming photos"""
    try:
        # Create date-based folder name (DD.MM format)
        date_folder = message.date.strftime("%d.%m")
        
        # Create local folder
        local_folder_path = os.path.join(BASE_DIR, date_folder)
        os.makedirs(local_folder_path, exist_ok=True)
        
        # Get the highest quality photo
        photo = message.photo[-1]
        
        # Debug info
        print(f"📸 Получено фото: file_id={photo.file_id}, size={photo.file_size}")
        
        # Determine filename based on caption
        if message.caption:
            # Use caption as filename, sanitized
            safe_caption = sanitize_filename(message.caption)
            filename = f"{safe_caption}.jpg"
        else:
            # Generate unique filename if no caption
            filename = f"photo_{uuid.uuid4().hex[:8]}.jpg"
        
        # Save photo locally
        local_file_path = os.path.join(local_folder_path, filename)
        
        # Download photo using aiogram 3 syntax
        print(f"💾 Сохраняю фото в: {local_file_path}")
        try:
            await bot.download(photo.file_id, local_file_path)
            print(f"✅ Фото скачано успешно")
        except Exception as download_error:
            print(f"❌ Ошибка скачивания: {download_error}")
            # Alternative method
            try:
                file_info = await bot.get_file(photo.file_id)
                file_path = file_info.file_path
                await bot.download_file(file_path, local_file_path)
                print(f"✅ Фото скачано альтернативным методом")
            except Exception as alt_error:
                print(f"❌ Альтернативный метод тоже не сработал: {alt_error}")
                raise alt_error
        
        # Upload to Google Drive if authenticated
        if drive_manager.service:
            try:
                # Create folder in Google Drive
                drive_folder_id = drive_manager.create_folder_if_not_exists(date_folder)
                
                # Upload file to Google Drive
                drive_file_id = drive_manager.upload_file(local_file_path, filename, drive_folder_id)
                
                # Send confirmation message
                print(
                    f"✅ Фото сохранено!\n"
                    f"📁 Папка: {date_folder}\n"
                    f"📄 Файл: {filename}\n"
                    f"💾 Локально: {local_file_path}\n"
                    f"☁️ Google Drive: загружено"
                )
            except Exception as e:
                print(
                    f"✅ Фото сохранено локально!\n"
                    f"📁 Папка: {date_folder}\n"
                    f"📄 Файл: {filename}\n"
                    f"❌ Ошибка Google Drive: {str(e)}"
                )
        else:
            # Send confirmation without Google Drive
            print(
                f"✅ Фото сохранено локально!\n"
                f"📁 Папка: {date_folder}\n"
                f"📄 Файл: {filename}\n"
                f"💾 Путь: {local_file_path}"
            )
            
    except Exception as e:
        print(f"❌ Ошибка при сохранении фото: {str(e)}")

@dp.message(Command("start"))
async def start_command(message: Message):
    """Handle /start command"""
    print(
        "🤖 Бот для сохранения фото\n\n"
        "📸 Отправьте фото с подписью или без неё\n"
        "📁 Фото будут сохранены в папки по дате (DD.MM)\n"
        "📄 Файлы будут названы по подписи или уникальным именем\n"
        "💾 Сохранение происходит локально и в Google Drive"
    )

@dp.message(Command("status"))
async def status_command(message: Message):
    """Handle /status command to check Google Drive connection"""
    if drive_manager.service:
        print("✅ Google Drive подключен")
    else:
        print("❌ Google Drive не подключен")

async def main():
    """Main function to start the bot"""
    print("🤖 Бот запущен!")
    
    # Try to authenticate with Google Drive
    if drive_manager.authenticate():
        print("✅ Google Drive подключен")
    else:
        print("❌ Google Drive не подключен - проверьте credentials.json")
    
    # Create base directory
    os.makedirs(BASE_DIR, exist_ok=True)
    
    # Start the bot
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

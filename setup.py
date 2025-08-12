#!/usr/bin/env python3
"""
Setup script for Telegram Photo Bot
"""

import os
import sys

def check_requirements():
    """Check if required packages are installed"""
    required_packages = [
        'aiogram',
        'google-auth',
        'google-auth-oauthlib',
        'google-api-python-client'
    ]
    
    # Check aiogram version specifically
    try:
        import aiogram
        version = aiogram.__version__
        if not version.startswith('3'):
            print(f"⚠️  Внимание: используется aiogram версии {version}, рекомендуется версия 3.x")
    except ImportError:
        pass
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Отсутствуют необходимые пакеты:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nУстановите их командой:")
        print("pip install -r requirements.txt")
        return False
    
    print("✅ Все необходимые пакеты установлены")
    return True

def check_files():
    """Check if required files exist"""
    print("\n📁 Проверка файлов:")
    
    # Check main.py
    if os.path.exists('main.py'):
        print("✅ main.py найден")
    else:
        print("❌ main.py не найден")
        return False
    
    # Check credentials.json
    if os.path.exists('credentials.json'):
        print("✅ credentials.json найден")
    else:
        print("❌ credentials.json не найден")
        print("   Скачайте его из Google Cloud Console")
        return False
    
    return True

def check_config():
    """Check bot configuration"""
    print("\n⚙️ Проверка конфигурации:")
    
    try:
        with open('main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check API token
        if 'API_TOKEN = "8092471614:AAFkfDjh6wW2OEmIKZ6JhIg6KCpRJ8JlsdU"' in content:
            print("✅ API токен настроен")
        else:
            print("❌ API токен не настроен")
            return False
        
        # Check Google Drive folder ID
        if 'GOOGLE_DRIVE_FOLDER_ID = "1-0vUx6wCEZrGxyACvBzMEISWVRIPvNgN"' in content:
            print("✅ Google Drive folder ID настроен")
        else:
            print("❌ Google Drive folder ID не настроен")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при проверке конфигурации: {e}")
        return False

def main():
    """Main setup function"""
    print("🤖 Настройка Telegram Photo Bot")
    print("=" * 40)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check files
    if not check_files():
        print("\n❌ Не все файлы найдены. См. README.md для инструкций.")
        sys.exit(1)
    
    # Check configuration
    if not check_config():
        print("\n❌ Конфигурация неполная. Проверьте настройки в main.py")
        sys.exit(1)
    
    print("\n✅ Все проверки пройдены!")
    print("\n🚀 Для запуска бота выполните:")
    print("python main.py")
    
    print("\n📖 Дополнительная информация:")
    print("- README.md - полная документация")
    print("- /start - команда для получения информации о боте")
    print("- /status - проверка подключения к Google Drive")

if __name__ == "__main__":
    main() 
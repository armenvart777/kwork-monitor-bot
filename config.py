import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    bot_token: str = os.getenv("BOT_TOKEN", "")
    check_interval: int = 300  # 5 минут

    default_keywords: list = field(default_factory=lambda: [
        "python", "питон", "telegram", "телеграм", "бот", "bot",
        "парсер", "парсинг", "скрипт", "script", "aiogram",
        "автоматизация", "automation", "scraping", "скрапинг",
        "api", "django", "flask", "fastapi", "selenium",
    ])

    default_categories: list = field(default_factory=lambda: [41])

    kwork_base_url: str = "https://kwork.ru"


settings = Settings()

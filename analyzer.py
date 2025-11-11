"""Анализатор заказов с биржи Kwork.

Оценивает сложность, бюджет, и даёт рекомендации по реализации.
Учитывает реальные навыки: Python, aiogram, парсинг, простые API.
Отсеивает: VPN/сети, DevOps, мобилки, блокчейн, фронтенд-фреймворки.
"""

from dataclasses import dataclass, field

# =============================================================
#  FEATURES — что умеем и что нет
# =============================================================

FEATURES = {
    # --- ТВОИ НАВЫКИ (can_do = True) ---
    "telegram_bot": {
        "keywords": ["телеграм", "telegram", "тг бот", "тг-бот", "aiogram", "telebot", "pyrogram"],
        "label": "Telegram-бот",
        "hours": 3,
        "can_do": True,
    },
    "database": {
        "keywords": ["база данных", "бд ", "sqlite", "postgresql", "postgres", "mysql", "mongodb", "хранение данных", "бд,"],
        "label": "База данных",
        "hours": 3,
        "can_do": True,
    },
    "admin_panel_basic": {
        "keywords": ["админка", "админ-панель", "панель управления", "управление через бот"],
        "label": "Админ-панель (в боте)",
        "hours": 5,
        "can_do": True,
    },
    "payments_single": {
        "keywords": ["приём оплаты", "прием оплаты", "юкасса", "yookassa", "yoomoney", "cryptobot", "telegram stars", "robokassa"],
        "label": "Оплата (1 система)",
        "hours": 5,
        "can_do": True,
    },
    "payments_multiple": {
        "keywords": ["несколько платежных", "несколько платёжных", "freekassa", "stripe", "paypal"],
        "label": "Оплата (несколько систем)",
        "hours": 12,
        "can_do": True,
    },
    "parsing": {
        "keywords": ["парсер", "парсинг", "scraping", "скрапинг", "beautifulsoup", "сбор данных", "спарсить", "парсить"],
        "label": "Парсинг / сбор данных",
        "hours": 5,
        "can_do": True,
    },
    "api_integration": {
        "keywords": ["google sheets", "crm", "подключить сервис", "интеграция с api", "webhook", "вебхук"],
        "label": "Интеграция с API",
        "hours": 4,
        "can_do": True,
    },
    "ocr": {
        "keywords": ["распознавание текста", "tesseract", "ocr"],
        "label": "OCR (распознавание текста)",
        "hours": 4,
        "can_do": True,
    },
    "ai_simple": {
        "keywords": ["chatgpt", "openai api", "gpt-4", "claude api", "нейросет", "генерация текста"],
        "label": "AI/GPT интеграция",
        "hours": 4,
        "can_do": True,
    },
    "notifications": {
        "keywords": ["уведомлени", "рассылк", "оповещени", "напоминани", "мониторинг"],
        "label": "Уведомления / рассылки",
        "hours": 3,
        "can_do": True,
    },
    "analytics": {
        "keywords": ["аналитик", "статистик", "график", "отчёт", "отчет", "дашборд", "dashboard"],
        "label": "Аналитика / отчёты",
        "hours": 4,
        "can_do": True,
    },
    "documents": {
        "keywords": ["документ", "шаблон", "docx", "word", "заполнение документ", "акт", "договор", "pdf генерац"],
        "label": "Работа с документами",
        "hours": 3,
        "can_do": True,
    },
    "filters_catalog": {
        "keywords": ["фильтр", "каталог", "подбор товар", "сортировка", "поиск товар", "чекбокс"],
        "label": "Фильтр / каталог товаров",
        "hours": 8,
        "can_do": True,
    },
    "subscriptions": {
        "keywords": ["подписк", "тариф", "тарифн", "посуточн", "ежедневн", "абонемент"],
        "label": "Подписки / тарифы",
        "hours": 5,
        "can_do": True,
    },
    "users_system": {
        "keywords": ["регистрац", "авторизац", "личный кабинет", "роли пользовател", "рекламодател"],
        "label": "Система пользователей / ролей",
        "hours": 5,
        "can_do": True,
    },
    "deploy_simple": {
        "keywords": ["деплой", "deploy", "запуск на серв", "бегет", "beget", "настрою на vps"],
        "label": "Деплой на сервер",
        "hours": 2,
        "can_do": True,
    },
    "selenium_browser": {
        "keywords": ["selenium", "playwright", "headless", "браузер автоматиз"],
        "label": "Браузерная автоматизация",
        "hours": 6,
        "can_do": True,
    },

    # --- НЕ ТВОИ НАВЫКИ (can_do = False) ---
    "vpn_proxy": {
        "keywords": [
            "xray", "v2ray", "vless", "vmess", "trojan", "reality", "xhttp",
            "shadowsocks", "wireguard", "openvpn", "vpn", "впн",
            "прокси", "proxy", "3x-ui", "marzban", "outline",
        ],
        "label": "VPN / прокси / сети",
        "hours": 15,
        "can_do": False,
    },
    "networking": {
        "keywords": [
            "балансировка серверов", "load balanc", "nginx настрой",
            "ядро xray", "ядром xray", "протокол reality", "протоколами",
            "iptables", "firewall", "dns настрой", "reverse proxy",
        ],
        "label": "Сетевая инфраструктура",
        "hours": 15,
        "can_do": False,
    },
    "devops_complex": {
        "keywords": [
            "kubernetes", "k8s", "docker compose", "ci/cd", "cicd",
            "jenkins", "gitlab ci", "terraform", "ansible",
            "оркестрация агентов", "оркестровая система",
        ],
        "label": "DevOps / оркестрация",
        "hours": 20,
        "can_do": False,
    },
    "ai_agents_complex": {
        "keywords": [
            "несколько ии агент", "несколько ai агент", "мультиагент",
            "вайбкодинг", "вайб-кодинг", "vibe coding", "vibecodin",
            "код ревью агент", "архитектур агент",
        ],
        "label": "AI-оркестрация / мультиагенты",
        "hours": 25,
        "can_do": False,
    },
    "web_frontend": {
        "keywords": ["react", "vue.js", "angular", "next.js", "nuxt", "svelte", "typescript фронт"],
        "label": "Фронтенд (React/Vue/Angular)",
        "hours": 15,
        "can_do": False,
    },
    "web_panel": {
        "keywords": ["веб-панель", "веб панель", "web-панель", "web панель", "веб-интерфейс", "web-интерфейс"],
        "label": "Веб-панель",
        "hours": 12,
        "can_do": False,
    },
    "mobile_app": {
        "keywords": [
            "мобильное приложение", "android приложен", "ios приложен",
            "flutter", "react native", "swift", "kotlin",
        ],
        "label": "Мобильное приложение",
        "hours": 30,
        "can_do": False,
    },
    "blockchain": {
        "keywords": [
            "блокчейн", "blockchain", "solidity", "smart contract",
            "смарт-контракт", "смарт контракт", "web3", "nft", "defi",
            "токен erc", "токен bep",
        ],
        "label": "Блокчейн / смарт-контракты",
        "hours": 20,
        "can_do": False,
    },
    "gamedev": {
        "keywords": ["unity", "unreal engine", "godot", "pygame", "разработка игр", "game dev", "gamedev"],
        "label": "Разработка игр",
        "hours": 25,
        "can_do": False,
    },
    "machine_learning": {
        "keywords": [
            "машинное обучение", "machine learning", "deep learning",
            "нейронная сеть обуч", "тренировка модел", "fine-tun",
            "pytorch", "tensorflow", "обучение модел",
        ],
        "label": "Machine Learning / обучение моделей",
        "hours": 25,
        "can_do": False,
    },
    "desktop_app": {
        "keywords": ["десктоп", "desktop", "gui приложен", "pyqt", "tkinter", "electron", "exe файл"],
        "label": "Десктоп-приложение",
        "hours": 15,
        "can_do": False,
    },
    "dorabotka_existing": {
        "keywords": ["доработка", "доработать", "допилить", "починить", "исправить баг", "фикс"],
        "label": "Доработка чужого кода",
        "hours": 6,
        "can_do": True,  # depends on context, but generally ok
    },
}

# Pricing tiers per hour
PRICE_PER_HOUR_MIN = 400
PRICE_PER_HOUR_FAIR = 800
PRICE_PER_HOUR_GOOD = 1500


@dataclass
class ProjectAnalysis:
    detected_features: list[str] = field(default_factory=list)
    difficulty: str = "?"
    difficulty_emoji: str = ""
    estimated_hours: int = 0
    fair_price_min: int = 0
    fair_price_max: int = 0
    budget_verdict: str = ""
    budget_emoji: str = ""
    can_do: bool = True
    blockers: list[str] = field(default_factory=list)  # features you CAN'T do
    can_do_text: str = ""
    how_to: str = ""
    recommendation: str = ""


def analyze_project(name: str, description: str, price_limit: int) -> ProjectAnalysis:
    """Analyze a Kwork project and return assessment."""
    text = f"{name} {description}".lower()
    result = ProjectAnalysis()

    # --- Detect features ---
    total_hours = 2  # base overhead
    detected_keys = []

    for key, feat in FEATURES.items():
        for kw in feat["keywords"]:
            if kw in text:
                if feat["label"] not in result.detected_features:
                    result.detected_features.append(feat["label"])
                    total_hours += feat["hours"]
                    detected_keys.append(key)
                    if not feat["can_do"]:
                        result.blockers.append(feat["label"])
                break

    # If multiple payment systems detected, don't double-count
    if "payments_single" in detected_keys and "payments_multiple" in detected_keys:
        total_hours -= 5  # remove single payment hours, keep multiple

    # Complexity multiplier: many features = more integration work
    feature_count = len(result.detected_features)
    if feature_count >= 5:
        total_hours = int(total_hours * 1.3)
    elif feature_count >= 3:
        total_hours = int(total_hours * 1.15)

    result.estimated_hours = total_hours

    # --- Difficulty ---
    if total_hours <= 5:
        result.difficulty = "лёгкий"
        result.difficulty_emoji = "🟢"
    elif total_hours <= 12:
        result.difficulty = "средний"
        result.difficulty_emoji = "🟡"
    elif total_hours <= 25:
        result.difficulty = "сложный"
        result.difficulty_emoji = "🟠"
    else:
        result.difficulty = "очень сложный"
        result.difficulty_emoji = "🔴"

    # --- Can you do it? ---
    if result.blockers:
        result.can_do = False
        blockers_str = ", ".join(result.blockers)
        result.can_do_text = f"❌ Не твой стек: {blockers_str}"
    else:
        result.can_do = True
        result.can_do_text = "✅ Можешь сделать с Claude"

    # --- Budget assessment ---
    result.fair_price_min = total_hours * PRICE_PER_HOUR_MIN
    result.fair_price_max = total_hours * PRICE_PER_HOUR_GOOD

    if price_limit <= 0:
        result.budget_verdict = "не указан"
        result.budget_emoji = "❓"
    elif price_limit >= total_hours * PRICE_PER_HOUR_GOOD:
        result.budget_verdict = "отличный"
        result.budget_emoji = "🤑"
    elif price_limit >= total_hours * PRICE_PER_HOUR_FAIR:
        result.budget_verdict = "хороший"
        result.budget_emoji = "👍"
    elif price_limit >= total_hours * PRICE_PER_HOUR_MIN:
        result.budget_verdict = "нормальный"
        result.budget_emoji = "👌"
    else:
        result.budget_verdict = "низковат"
        result.budget_emoji = "⚠️"

    # --- How to (стек / план) ---
    STACK_MAP = {
        "telegram_bot": "aiogram 3",
        "database": "aiosqlite/PostgreSQL",
        "admin_panel_basic": "inline-кнопки админка",
        "payments_single": "ЮKassa / CryptoBot",
        "payments_multiple": "FreeKassa + Stripe + PayPal + YooMoney",
        "parsing": "aiohttp + BeautifulSoup",
        "api_integration": "aiohttp + REST API",
        "ocr": "pytesseract",
        "ai_simple": "OpenAI / Claude API",
        "notifications": "asyncio scheduler",
        "analytics": "matplotlib / PDF",
        "documents": "python-docx / PDF",
        "filters_catalog": "inline-кнопки + фильтрация в БД",
        "subscriptions": "система подписок + cron списание",
        "users_system": "роли + регистрация",
        "deploy_simple": "VPS/Beget",
        "selenium_browser": "Selenium / Playwright",
        "dorabotka_existing": "рефакторинг чужого кода",
    }

    steps = []
    for key in detected_keys:
        if key in STACK_MAP:
            steps.append(STACK_MAP[key])
    if not steps:
        steps.append("Python по ТЗ")

    result.how_to = ", ".join(steps)

    # --- Recommendation ---
    if not result.can_do:
        if len(result.blockers) >= 2:
            result.recommendation = "🚫 Пропускай — далеко от твоего стека"
        else:
            result.recommendation = "⚠️ Рискованно — есть незнакомые технологии"
    elif result.budget_verdict == "низковат" and result.difficulty in ("сложный", "очень сложный"):
        result.recommendation = "⚠️ Мало платят за сложную работу"
    elif result.budget_verdict in ("отличный", "хороший") and result.can_do:
        result.recommendation = "🔥 Бери! Хороший заказ"
    elif result.difficulty == "лёгкий" and result.can_do:
        result.recommendation = "👍 Простой — хорош для отзыва"
    elif result.difficulty == "средний" and result.can_do:
        result.recommendation = "👌 Можно брать"
    elif result.can_do:
        result.recommendation = "👌 Можно брать, но оцени сроки"
    else:
        result.recommendation = "🤔 Подумай хорошо перед откликом"

    return result


def format_analysis(a: ProjectAnalysis) -> str:
    """Format analysis as HTML text for Telegram."""
    features = ", ".join(a.detected_features) if a.detected_features else "не определены"
    fair = f"{a.fair_price_min:,}–{a.fair_price_max:,} ₽".replace(",", " ")

    lines = [
        f"\n{'─' * 28}",
        f"🤖 <b>Анализ заказа:</b>",
        f"",
        f"{a.difficulty_emoji} Сложность: <b>{a.difficulty}</b> (~{a.estimated_hours}ч)",
        f"{a.budget_emoji} Бюджет: <b>{a.budget_verdict}</b> (справедливо: {fair})",
        f"{a.can_do_text}",
        f"",
        f"🔧 Что нужно: {features}",
        f"🛠 Стек: {a.how_to}",
        f"",
        f"<b>{a.recommendation}</b>",
    ]

    return "\n".join(lines)

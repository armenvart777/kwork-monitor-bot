from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData


class ModeCB(CallbackData, prefix="mode"):
    mode: str


class ActionCB(CallbackData, prefix="act"):
    action: str


class BudgetCB(CallbackData, prefix="budget"):
    amount: int


class OffersCB(CallbackData, prefix="offers"):
    count: int


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🔍 Новые заказы",
                callback_data=ActionCB(action="check_new").pack(),
            ),
            InlineKeyboardButton(
                text="📋 Все заказы",
                callback_data=ActionCB(action="check_all").pack(),
            ),
        ],
        [InlineKeyboardButton(
            text="⚙️ Настройки",
            callback_data=ActionCB(action="settings").pack(),
        )],
        [InlineKeyboardButton(
            text="📊 Статус",
            callback_data=ActionCB(action="status").pack(),
        )],
    ])


def settings_kb(current_mode: str, monitoring_active: bool) -> InlineKeyboardMarkup:
    mode_text = "📈 Отзывы" if current_mode == "reviews" else "💰 Заработок"
    mon_text = "✅ Мониторинг ВКЛ" if monitoring_active else "❌ Мониторинг ВЫКЛ"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"Режим: {mode_text}",
            callback_data=ActionCB(action="change_mode").pack(),
        )],
        [InlineKeyboardButton(
            text=mon_text,
            callback_data=ActionCB(action="toggle_monitoring").pack(),
        )],
        [InlineKeyboardButton(
            text="💰 Мин. бюджет",
            callback_data=ActionCB(action="set_budget").pack(),
        )],
        [InlineKeyboardButton(
            text="🔑 Ключевые слова",
            callback_data=ActionCB(action="show_keywords").pack(),
        )],
        [InlineKeyboardButton(
            text="👥 Макс. откликов",
            callback_data=ActionCB(action="set_max_offers").pack(),
        )],
        [InlineKeyboardButton(
            text="🗑 Сбросить историю просмотров",
            callback_data=ActionCB(action="clear_seen").pack(),
        )],
        [InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=ActionCB(action="back_main").pack(),
        )],
    ])


def mode_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📈 Наращиваю отзывы (всё подряд)",
            callback_data=ModeCB(mode="reviews").pack(),
        )],
        [InlineKeyboardButton(
            text="💰 Зарабатываю (от мин. бюджета)",
            callback_data=ModeCB(mode="earning").pack(),
        )],
        [InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=ActionCB(action="settings").pack(),
        )],
    ])


def budget_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="0 ₽ (любой)",
                callback_data=BudgetCB(amount=0).pack(),
            ),
            InlineKeyboardButton(
                text="1 000 ₽",
                callback_data=BudgetCB(amount=1000).pack(),
            ),
        ],
        [
            InlineKeyboardButton(
                text="3 000 ₽",
                callback_data=BudgetCB(amount=3000).pack(),
            ),
            InlineKeyboardButton(
                text="5 000 ₽",
                callback_data=BudgetCB(amount=5000).pack(),
            ),
        ],
        [
            InlineKeyboardButton(
                text="10 000 ₽",
                callback_data=BudgetCB(amount=10000).pack(),
            ),
            InlineKeyboardButton(
                text="15 000 ₽",
                callback_data=BudgetCB(amount=15000).pack(),
            ),
        ],
        [InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=ActionCB(action="settings").pack(),
        )],
    ])


def offers_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="0 (любое)",
                callback_data=OffersCB(count=0).pack(),
            ),
            InlineKeyboardButton(
                text="до 5",
                callback_data=OffersCB(count=5).pack(),
            ),
        ],
        [
            InlineKeyboardButton(
                text="до 10",
                callback_data=OffersCB(count=10).pack(),
            ),
            InlineKeyboardButton(
                text="до 20",
                callback_data=OffersCB(count=20).pack(),
            ),
        ],
        [
            InlineKeyboardButton(
                text="до 30",
                callback_data=OffersCB(count=30).pack(),
            ),
            InlineKeyboardButton(
                text="до 50",
                callback_data=OffersCB(count=50).pack(),
            ),
        ],
        [InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=ActionCB(action="settings").pack(),
        )],
    ])


def project_kb(project_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Откликнуться на Kwork", url=project_url)],
    ])


def keywords_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="➕ Добавить",
                callback_data=ActionCB(action="add_kw").pack(),
            ),
            InlineKeyboardButton(
                text="➖ Удалить",
                callback_data=ActionCB(action="rm_kw").pack(),
            ),
        ],
        [InlineKeyboardButton(
            text="🔄 Сбросить по умолчанию",
            callback_data=ActionCB(action="reset_kw").pack(),
        )],
        [InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=ActionCB(action="settings").pack(),
        )],
    ])

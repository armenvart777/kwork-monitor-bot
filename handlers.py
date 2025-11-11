import logging

from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import db
from config import settings
from keyboards import (
    main_menu_kb, settings_kb, mode_kb, budget_kb, offers_kb, project_kb, keywords_kb,
    ActionCB, ModeCB, BudgetCB, OffersCB,
)
from scraper import fetch_kwork_projects, filter_projects
from analyzer import analyze_project, format_analysis

logger = logging.getLogger(__name__)
router = Router()


# --- FSM States ---

class AddKeyword(StatesGroup):
    waiting = State()


class RemoveKeyword(StatesGroup):
    waiting = State()


# --- Helpers ---

async def is_admin(user_id: int) -> bool:
    admin_id = await db.get_admin_id()
    return admin_id is None or admin_id == user_id


def format_project(project) -> str:
    budget = f"{project.price_limit:,}".replace(",", " ")
    possible = ""
    if project.possible_price_limit > project.price_limit:
        p = f"{project.possible_price_limit:,}".replace(",", " ")
        possible = f" (допуст. до {p} ₽)"

    desc = project.description
    if len(desc) > 300:
        desc = desc[:300] + "..."

    hire = ""
    if project.hire_percent:
        hire = f"\n✅ Нанято: {project.hire_percent}%"

    analysis = analyze_project(project.name, project.description, project.price_limit)
    analysis_text = format_analysis(analysis)

    return (
        f"🆕 <b>Заказ на бирже</b>\n\n"
        f"📋 <b>{project.name}</b>\n"
        f"💰 Бюджет: до <b>{budget} ₽</b>{possible}\n"
        f"⏰ Осталось: {project.time_left}\n"
        f"👥 Предложений: {project.offers_count}{hire}\n\n"
        f"📝 {desc}"
        f"{analysis_text}"
    )


# ==========================================
#  COMMANDS
# ==========================================

@router.message(CommandStart())
async def cmd_start(message: Message):
    admin_id = await db.get_admin_id()
    if admin_id is None:
        await db.set_admin_id(message.from_user.id)
    elif admin_id != message.from_user.id:
        await message.answer("⛔ Бот только для владельца.")
        return

    await message.answer(
        "👋 <b>Kwork Monitor Bot</b>\n\n"
        "Отслеживаю биржу Kwork и присылаю подходящие заказы.\n\n"
        "🔍 <b>Новые заказы</b> — только непрочитанные\n"
        "📋 <b>Все заказы</b> — все подходящие на бирже\n"
        "⚙️ <b>Настройки</b> — режим, бюджет, слова\n"
        "📊 <b>Статус</b> — текущее состояние\n\n"
        f"Автопроверка каждые {settings.check_interval // 60} мин.",
        reply_markup=main_menu_kb(),
    )


@router.message(Command("check"))
async def cmd_check(message: Message):
    if not await is_admin(message.from_user.id):
        return
    await _do_check(message.bot, message.chat.id, only_new=True)


@router.message(Command("all"))
async def cmd_all(message: Message):
    if not await is_admin(message.from_user.id):
        return
    await _do_check(message.bot, message.chat.id, only_new=False)


@router.message(Command("settings"))
async def cmd_settings(message: Message):
    if not await is_admin(message.from_user.id):
        return
    mode = await db.get_mode()
    active = await db.is_monitoring_active()
    await message.answer(
        "⚙️ <b>Настройки</b>",
        reply_markup=settings_kb(mode, active),
    )


@router.message(Command("status"))
async def cmd_status(message: Message):
    if not await is_admin(message.from_user.id):
        return
    await _send_status(message)


# ==========================================
#  CALLBACKS: Navigation
# ==========================================

@router.callback_query(ActionCB.filter(F.action == "back_main"))
async def cb_back_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "👋 <b>Kwork Monitor Bot</b>\n\nВыбери действие:",
        reply_markup=main_menu_kb(),
    )
    await callback.answer()


@router.callback_query(ActionCB.filter(F.action == "settings"))
async def cb_settings(callback: CallbackQuery):
    mode = await db.get_mode()
    active = await db.is_monitoring_active()
    await callback.message.edit_text(
        "⚙️ <b>Настройки</b>",
        reply_markup=settings_kb(mode, active),
    )
    await callback.answer()


@router.callback_query(ActionCB.filter(F.action == "status"))
async def cb_status(callback: CallbackQuery):
    await _send_status_edit(callback)
    await callback.answer()


# ==========================================
#  CALLBACKS: Check orders
# ==========================================

@router.callback_query(ActionCB.filter(F.action == "check_new"))
async def cb_check_new(callback: CallbackQuery):
    await callback.answer("🔍 Проверяю биржу...")
    await _do_check(callback.bot, callback.message.chat.id, only_new=True)


@router.callback_query(ActionCB.filter(F.action == "check_all"))
async def cb_check_all(callback: CallbackQuery):
    await callback.answer("📋 Загружаю все заказы...")
    await _do_check(callback.bot, callback.message.chat.id, only_new=False)


# ==========================================
#  CALLBACKS: Mode
# ==========================================

@router.callback_query(ActionCB.filter(F.action == "change_mode"))
async def cb_change_mode(callback: CallbackQuery):
    await callback.message.edit_text(
        "📊 <b>Выбери режим работы:</b>\n\n"
        "📈 <b>Отзывы</b> — показываю все подходящие (даже дешёвые)\n"
        "💰 <b>Заработок</b> — только от минимального бюджета",
        reply_markup=mode_kb(),
    )
    await callback.answer()


@router.callback_query(ModeCB.filter())
async def cb_set_mode(callback: CallbackQuery, callback_data: ModeCB):
    await db.set_mode(callback_data.mode)
    name = "📈 Наращиваю отзывы" if callback_data.mode == "reviews" else "💰 Зарабатываю"
    await callback.answer(f"Режим: {name}", show_alert=True)

    mode = await db.get_mode()
    active = await db.is_monitoring_active()
    await callback.message.edit_text(
        "⚙️ <b>Настройки</b>",
        reply_markup=settings_kb(mode, active),
    )


# ==========================================
#  CALLBACKS: Monitoring toggle
# ==========================================

@router.callback_query(ActionCB.filter(F.action == "toggle_monitoring"))
async def cb_toggle(callback: CallbackQuery):
    active = await db.is_monitoring_active()
    await db.set_monitoring_active(not active)
    status = "✅ Мониторинг включён" if not active else "❌ Мониторинг выключен"
    await callback.answer(status, show_alert=True)

    mode = await db.get_mode()
    new_active = await db.is_monitoring_active()
    await callback.message.edit_text(
        "⚙️ <b>Настройки</b>",
        reply_markup=settings_kb(mode, new_active),
    )


# ==========================================
#  CALLBACKS: Budget
# ==========================================

@router.callback_query(ActionCB.filter(F.action == "set_budget"))
async def cb_set_budget(callback: CallbackQuery):
    current = await db.get_min_budget()
    cur_text = f"{current:,} ₽".replace(",", " ") if current else "любой"
    await callback.message.edit_text(
        f"💰 <b>Минимальный бюджет заказа</b>\n\n"
        f"Сейчас: <b>{cur_text}</b>\n"
        f"Заказы дешевле — не покажу.",
        reply_markup=budget_kb(),
    )
    await callback.answer()


@router.callback_query(BudgetCB.filter())
async def cb_budget_set(callback: CallbackQuery, callback_data: BudgetCB):
    await db.set_min_budget(callback_data.amount)
    text = f"{callback_data.amount:,} ₽".replace(",", " ") if callback_data.amount else "любой"
    await callback.answer(f"Мин. бюджет: {text}", show_alert=True)

    mode = await db.get_mode()
    active = await db.is_monitoring_active()
    await callback.message.edit_text(
        "⚙️ <b>Настройки</b>",
        reply_markup=settings_kb(mode, active),
    )


# ==========================================
#  CALLBACKS: Max offers
# ==========================================

@router.callback_query(ActionCB.filter(F.action == "set_max_offers"))
async def cb_set_max_offers(callback: CallbackQuery):
    current = await db.get_max_offers()
    cur_text = f"до {current}" if current else "любое"
    await callback.message.edit_text(
        f"👥 <b>Макс. количество откликов</b>\n\n"
        f"Сейчас: <b>{cur_text}</b>\n"
        f"Заказы с большим числом откликов — не покажу.\n"
        f"(Если много откликов — шансы ниже)",
        reply_markup=offers_kb(),
    )
    await callback.answer()


@router.callback_query(OffersCB.filter())
async def cb_offers_set(callback: CallbackQuery, callback_data: OffersCB):
    await db.set_max_offers(callback_data.count)
    text = f"до {callback_data.count}" if callback_data.count else "любое"
    await callback.answer(f"Макс. откликов: {text}", show_alert=True)

    mode = await db.get_mode()
    active = await db.is_monitoring_active()
    await callback.message.edit_text(
        "⚙️ <b>Настройки</b>",
        reply_markup=settings_kb(mode, active),
    )


# ==========================================
#  CALLBACKS: Keywords
# ==========================================

@router.callback_query(ActionCB.filter(F.action == "show_keywords"))
async def cb_show_keywords(callback: CallbackQuery):
    keywords = await db.get_keywords() or settings.default_keywords
    kw_list = ", ".join(keywords)

    await callback.message.edit_text(
        f"🔑 <b>Ключевые слова</b>\n\n"
        f"Ищу заказы, содержащие:\n<code>{kw_list}</code>",
        reply_markup=keywords_kb(),
    )
    await callback.answer()


@router.callback_query(ActionCB.filter(F.action == "add_kw"))
async def cb_add_kw(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "✏️ Отправь слово (или несколько через запятую):"
    )
    await state.set_state(AddKeyword.waiting)
    await callback.answer()


@router.message(AddKeyword.waiting)
async def process_add_kw(message: Message, state: FSMContext):
    new = [kw.strip().lower() for kw in message.text.split(",") if kw.strip()]
    current = await db.get_keywords() or list(settings.default_keywords)

    added = [kw for kw in new if kw not in current]
    current.extend(added)
    await db.set_keywords(current)
    await state.clear()

    if added:
        await message.answer(
            f"✅ Добавлено: {', '.join(added)}",
            reply_markup=main_menu_kb(),
        )
    else:
        await message.answer(
            "Эти слова уже есть в списке.",
            reply_markup=main_menu_kb(),
        )


@router.callback_query(ActionCB.filter(F.action == "rm_kw"))
async def cb_rm_kw(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("✏️ Какое слово удалить?")
    await state.set_state(RemoveKeyword.waiting)
    await callback.answer()


@router.message(RemoveKeyword.waiting)
async def process_rm_kw(message: Message, state: FSMContext):
    word = message.text.strip().lower()
    current = await db.get_keywords() or list(settings.default_keywords)

    if word in current:
        current.remove(word)
        await db.set_keywords(current)
        await message.answer(f"✅ Удалено: {word}", reply_markup=main_menu_kb())
    else:
        await message.answer(f"❌ «{word}» не найдено", reply_markup=main_menu_kb())

    await state.clear()


@router.callback_query(ActionCB.filter(F.action == "reset_kw"))
async def cb_reset_kw(callback: CallbackQuery):
    await db.set_keywords(list(settings.default_keywords))
    await callback.answer("🔄 Ключевые слова сброшены", show_alert=True)

    kw_list = ", ".join(settings.default_keywords)
    await callback.message.edit_text(
        f"🔑 <b>Ключевые слова</b>\n\n"
        f"Ищу заказы, содержащие:\n<code>{kw_list}</code>",
        reply_markup=keywords_kb(),
    )


# ==========================================
#  CALLBACKS: Clear seen history
# ==========================================

@router.callback_query(ActionCB.filter(F.action == "clear_seen"))
async def cb_clear_seen(callback: CallbackQuery):
    count = await db.get_seen_count()
    await db.clear_seen_projects()
    await callback.answer(
        f"🗑 Очищено! Было {count} записей.\n"
        f"Теперь все заказы покажутся как новые.",
        show_alert=True,
    )
    mode = await db.get_mode()
    active = await db.is_monitoring_active()
    await callback.message.edit_text(
        "⚙️ <b>Настройки</b>",
        reply_markup=settings_kb(mode, active),
    )


# ==========================================
#  CORE: Check logic
# ==========================================

async def _do_check(bot: Bot, chat_id: int, only_new: bool = True, silent: bool = False):
    """Check Kwork exchange for matching projects.

    only_new=True  — show only unseen projects (for auto-check and 'Новые')
    only_new=False — show ALL matching projects (for 'Все заказы')
    silent=True    — don't send message if no new projects (for scheduled checks)
    """
    categories = await db.get_categories() or settings.default_categories
    keywords = await db.get_keywords() or settings.default_keywords
    mode = await db.get_mode()
    min_budget = await db.get_min_budget() if mode == "earning" else 0
    max_offers = await db.get_max_offers()

    try:
        all_projects = await fetch_kwork_projects(categories)
    except Exception as e:
        logger.error("Scraper error: %s", e)
        if not silent:
            await bot.send_message(chat_id, f"❌ Ошибка загрузки биржи: {e}")
        return

    if not all_projects:
        if not silent:
            await bot.send_message(
                chat_id,
                "🔍 Не удалось загрузить заказы с биржи. Попробуй позже.",
                reply_markup=main_menu_kb(),
            )
        return

    matched = filter_projects(all_projects, keywords, min_budget, max_offers)

    if only_new:
        # Filter out already seen, mark new ones as seen
        projects_to_show = []
        for project in matched:
            if not await db.is_project_seen(project.id):
                projects_to_show.append(project)
                await db.mark_project_seen(
                    project.id, project.name, str(project.price_limit)
                )
    else:
        # Show all matching — but still mark them as seen for future
        projects_to_show = matched
        for project in matched:
            await db.mark_project_seen(
                project.id, project.name, str(project.price_limit)
            )

    label = "новых" if only_new else "подходящих"

    if not projects_to_show:
        if silent:
            return
        await bot.send_message(
            chat_id,
            f"🔍 Проверил биржу.\n\n"
            f"Всего на бирже: <b>{len(all_projects)}</b>\n"
            f"Подходящих: <b>{len(matched)}</b>\n"
            f"Новых: <b>0</b>\n\n"
            f"{'Все подходящие уже были показаны ранее.' if matched else 'Нет заказов по твоим ключевым словам.'}",
            reply_markup=main_menu_kb(),
        )
        return

    await bot.send_message(
        chat_id,
        f"🔍 Найдено {label}: <b>{len(projects_to_show)}</b> "
        f"(из {len(all_projects)} на бирже)",
    )

    for project in projects_to_show:
        try:
            await bot.send_message(
                chat_id,
                format_project(project),
                reply_markup=project_kb(project.url),
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.error("Error sending project %d: %s", project.id, e)


# ==========================================
#  Status
# ==========================================

async def _send_status(message: Message):
    mode = await db.get_mode()
    min_b = await db.get_min_budget()
    active = await db.is_monitoring_active()
    seen = await db.get_seen_count()
    keywords = await db.get_keywords() or settings.default_keywords

    mode_t = "📈 Наращиваю отзывы" if mode == "reviews" else "💰 Зарабатываю"
    status_t = "✅ Активен" if active else "❌ Остановлен"
    budget_t = f"{min_b:,} ₽".replace(",", " ") if min_b else "любой"

    await message.answer(
        f"📊 <b>Статус мониторинга</b>\n\n"
        f"Состояние: {status_t}\n"
        f"Режим: {mode_t}\n"
        f"Мин. бюджет: {budget_t}\n"
        f"Ключевых слов: {len(keywords)}\n"
        f"Просмотрено заказов: {seen}\n"
        f"Интервал: каждые {settings.check_interval // 60} мин",
        reply_markup=main_menu_kb(),
    )


async def _send_status_edit(callback: CallbackQuery):
    mode = await db.get_mode()
    min_b = await db.get_min_budget()
    active = await db.is_monitoring_active()
    seen = await db.get_seen_count()
    keywords = await db.get_keywords() or settings.default_keywords

    mode_t = "📈 Наращиваю отзывы" if mode == "reviews" else "💰 Зарабатываю"
    status_t = "✅ Активен" if active else "❌ Остановлен"
    budget_t = f"{min_b:,} ₽".replace(",", " ") if min_b else "любой"

    await callback.message.edit_text(
        f"📊 <b>Статус мониторинга</b>\n\n"
        f"Состояние: {status_t}\n"
        f"Режим: {mode_t}\n"
        f"Мин. бюджет: {budget_t}\n"
        f"Ключевых слов: {len(keywords)}\n"
        f"Просмотрено заказов: {seen}\n"
        f"Интервал: каждые {settings.check_interval // 60} мин",
        reply_markup=main_menu_kb(),
    )

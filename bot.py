import logging
import os
import asyncio
import threading

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# Импортируем Flask-приложение, db и модели из apppl.py
from apppl import create_app, db, FranchiseApplication
# Импортируем TelegramUser из models.py
from models import TelegramUser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем Flask-приложение (один раз) и сохраняем в глобальной переменной
flask_app = create_app()

# Глобальная переменная для телеграм-бота
application: Application = None

# Событие, сигнализирующее о готовности бота
bot_ready = threading.Event()

# Словарь локализации для бота
BOT_TEXTS = {
    'ru': {
        'start': "Привет! Я бот Han Tandyr. Используйте /myrequests для просмотра заявок.",
        'admin_notify': "Новая заявка #{app_id} от {firstname} {lastname}. Телефон: {phone}",
        'my_requests_none': "У вас нет заявок.",
        'my_requests_header': "Ваши заявки:",
        'my_requests_item': "#{app_id}: {firstname} {lastname}, телефон {phone}",
        'unknown': "Неизвестная команда.",
        'help': "Доступные команды: /start, /help, /myrequests, /setadmin @username",
        'no_permission': "У вас нет прав для выполнения этой команды.",
        'setadmin_usage': "Используйте: /setadmin @username",
        'setadmin_ok': "Пользователь @{handle} теперь администратор."
    },
    'en': {
        'start': "Hello! I'm the Han Tandyr bot. Use /myrequests to view your applications.",
        'admin_notify': "New application #{app_id} from {firstname} {lastname}, phone: {phone}",
        'my_requests_none': "You have no applications.",
        'my_requests_header': "Your applications:",
        'my_requests_item': "#{app_id}: {firstname} {lastname}, phone {phone}",
        'unknown': "Unknown command.",
        'help': "Available commands: /start, /help, /myrequests, /setadmin @username",
        'no_permission': "You do not have permission for this command.",
        'setadmin_usage': "Usage: /setadmin @username",
        'setadmin_ok': "User @{handle} is now an administrator."
    },
    'kk': {
        'start': "Сәлем! Бұл Han Tandyr боты. /myrequests арқылы өтінімдеріңізді көре аласыз.",
        'admin_notify': "Жаңа өтінім #{app_id} {firstname} {lastname} -дан, телефон: {phone}",
        'my_requests_none': "Сіздің өтінімдеріңіз жоқ.",
        'my_requests_header': "Сіздің өтінімдеріңіз:",
        'my_requests_item': "#{app_id}: {firstname} {lastname}, телефон {phone}",
        'unknown': "Белгісіз команда.",
        'help': "Қол жетімді командалар: /start, /help, /myrequests, /setadmin @username",
        'no_permission': "Осы команданы орындауға рұқсатыңыз жоқ.",
        'setadmin_usage': "Пайдалану: /setadmin @username",
        'setadmin_ok': "Пайдаланушы @{handle} енді әкімші."
    },
    'zh': {
        'start': "你好！我是 Han Tandyr 机器人。使用 /myrequests 查看您的申请。",
        'admin_notify': "新的申请 #{app_id} 来自 {firstname} {lastname}，电话：{phone}",
        'my_requests_none': "您没有任何申请。",
        'my_requests_header': "您的申请：",
        'my_requests_item': "#{app_id}: {firstname} {lastname}, 电话 {phone}",
        'unknown': "未知命令。",
        'help': "Available commands: /start, /help, /myrequests, /setadmin @username",
        'no_permission': "您没有使用此命令的权限。",
        'setadmin_usage': "用法: /setadmin @username",
        'setadmin_ok': "用户 @{handle} 现为管理员。"
    },
    'ar': {
        'start': "مرحباً! أنا بوت Han Tandyr. استخدم /myrequests للاطلاع على طلباتك.",
        'admin_notify': "طلب جديد رقم #{app_id} من {firstname} {lastname}، هاتف: {phone}",
        'my_requests_none': "ليس لديك أي طلبات.",
        'my_requests_header': "طلباتك:",
        'my_requests_item': "#{app_id}: {firstname} {lastname}، هاتف {phone}",
        'unknown': "أمر غير معروف.",
        'help': "Available commands: /start, /help, /myrequests, /setadmin @username",
        'no_permission': "ليست لديك صلاحية لتنفيذ هذا الأمر.",
        'setadmin_usage': "الاستخدام: /setadmin @username",
        'setadmin_ok': "المستخدم @{handle} أصبح الآن مديراً."
    },
}

def get_text(lang: str, key: str, **kwargs) -> str:
    if lang not in BOT_TEXTS:
        lang = 'en'
    template = BOT_TEXTS[lang].get(key, key)
    return template.format(**kwargs)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = 'ru'
    text = get_text(lang, 'start')
    await update.message.reply_text(text)

async def myrequests_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = (update.effective_user.username or "").lower()
    with flask_app.app_context():
        apps = FranchiseApplication.query.filter_by(telegram_handle=username).all()
    lang = 'ru'
    if not apps:
        await update.message.reply_text(get_text(lang, 'my_requests_none'))
        return
    lines = [get_text(lang, 'my_requests_header')]
    for a in apps:
        line = get_text(
            lang,
            'my_requests_item',
            app_id=a.id,
            firstname=a.firstname,
            lastname=a.lastname,
            phone=a.phone
        )
        lines.append(line)
    await update.message.reply_text("\n".join(lines))

async def setadmin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = (update.effective_user.username or "").lower()
    lang = 'ru'
    with flask_app.app_context():
        user = TelegramUser.query.filter_by(username=username).first()
    if not user or not getattr(user, "is_admin", False):
        await update.message.reply_text(get_text(lang, 'no_permission'))
        return
    if not context.args:
        await update.message.reply_text(get_text(lang, 'setadmin_usage'))
        return
    handle = context.args[0].lstrip('@').lower()
    with flask_app.app_context():
        tuser = TelegramUser.query.filter_by(username=handle).first()
        if tuser:
            tuser.is_admin = True
        else:
            tuser = TelegramUser(username=handle, chat_id=0, is_admin=True)
            db.session.add(tuser)
        db.session.commit()
    await update.message.reply_text(get_text(lang, 'setadmin_ok', handle=handle))

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_text('ru', 'unknown'))

async def notify_new_application(app_id: int):
    # Ждем, пока бот будет готов (до 10 секунд)
    bot_ready.wait(timeout=10)
    with flask_app.app_context():
        app_data = FranchiseApplication.query.get(app_id)
        if not app_data:
            return
        lang = app_data.lang
        text = get_text(
            lang,
            'admin_notify',
            app_id=app_data.id,
            firstname=app_data.firstname,
            lastname=app_data.lastname,
            phone=app_data.phone,
        )
    for admin_id in [1574946637]:
        try:
            await application.bot.send_message(chat_id=admin_id, text=text)
        except Exception as e:
            logger.warning(f"Failed to send message to admin {admin_id}: {e}")


def run_bot():
    global application
    token = '7394116552:AAGJKNssUPj6d7HHaoK3UotHCsIt37jhsn0'
    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("myrequests", myrequests_command))
    application.add_handler(CommandHandler("setadmin", setadmin_command))
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    # Сигнализируем, что бот готов
    bot_ready.set()

    application.run_polling()
if __name__ == "__main__":
    run_bot()

from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, \
    CallbackQueryHandler, ConversationHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import sqlite3 as sql
from text_moderation import *
import logging

# ТОКЕН бота в телеграмме @CookingTogetherBot
TOKEN = "1147988782:AAFbcmCE96UICmS3_yrYGXLqQ1FjyjNkZCg"

# Подключение базы данных SQLite3 с рецептами
conn = sql.connect("db/CookingBook.sqlite", check_same_thread=False)
cursor = conn.cursor()

# Создание оперативного массива с категориями из базы данных
cursor.execute('select name from Category')
categories = [i[0] for i in cursor.fetchall()]

# Настройка и инициализация логов для отлаживания и контроля программы
# Выводит время и дату события с описанием
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Оперативный массив для рецептов из категорий
data_from_db, actual_message_id = [], 0
# Stages
FIRST, SECOND = range(2)
# Callback data
ONE, TWO, THREE, FOUR = range(4)


def start(update, context):
    logger.info("User %s started the conversation.", update.message.from_user.first_name)

    keyboard = [[InlineKeyboardButton(categories[i], callback_data=i)]
                for i in range(len(categories))]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Выберите категорию рецептов:', reply_markup=reply_markup)

    logging.info("Sent to @%s Message of '/start' state.", update.message.from_user.first_name)
    return FIRST


def start_over(update, context):
    query = update.callback_query
    # logger.info("Waiting user's answer...", update.message.from_user.first_name)
    query.answer()
    # logger.info("User %s restarted the conversation.", update.message.from_user.first_name)

    keyboard = [[InlineKeyboardButton(categories[i], callback_data=i)]
                for i in range(len(categories))]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.edit_message_text(text='Выберите категорию рецептов:', reply_markup=reply_markup)
    logging.info("Edited @%s Message '/start' state.", query.from_user.first_name)

    return FIRST


def one(update, context):
    global data_from_db, actual_message_id
    query = update.callback_query
    logger.info("Waiting @%s's answer...", query.from_user.first_name)

    query.answer()
    logger.info("Got answer from @%s: '{}'.".format(query.data), query.from_user.first_name)

    keyboard = [[InlineKeyboardButton('Выбрать другую  категорию', callback_data='1')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    cursor.execute("select name from Book where id_category='{}'".format(query.data))
    data_from_db = cursor.fetchall()

    text = 'Вот список блюд в категории {}'.format(categories[int(query.data)])
    for pos in range(len(data_from_db)):
        text = text + f'\n{pos + 1}) {data_from_db[pos][0].strip()}'
    text = text + f'\nНапишите в чат номер нужного рецепта или выберите другую категорию.'

    actual_message_id = query.message.message_id
    query.bot.edit_message_text(text, chat_id=query.message.chat_id,
                                message_id=query.message.message_id,
                                reply_markup=reply_markup)
    logging.info("Edited @%s Message FIRST state.", query.from_user.first_name)
    return SECOND


def get_receipt_number(update, context):
    global data_from_db, actual_message_id
    receipt = update.message.text
    logger.info("Got Message '{}' from @%s.".format(receipt), update.message.from_user.first_name)

    cursor.execute("select name, ingredients, cooking, image_url from Book where name=?",
                   data_from_db[int(receipt) - 1])
    data_from_db = cursor.fetchall()[0]
    name, ingredients, cooking, image_url = data_from_db
    name, ingredients = format_name(name), format_ingredients(ingredients).strip()

    cap = f"{name}\n" \
        f"СОСТАВ:\n{ingredients}\n" \
        f"ПРИГОТОВЛЕНИЕ:\n{cooking}"

    # context.bot.edit_message_text(text="Приятного аппетита!",
    #                               chat_id=update.message.chat_id,
    #                               message_id=actual_message_id,
    #                               reply_markup=None,
    #                               )
    # logging.info("Edited @%s Message SECOND state.", update.message.from_user.first_name)

    context.bot.delete_message(update.message.chat_id, actual_message_id)
    logging.info("Deleted @%s Message SECOND state.", update.message.from_user.first_name)

    if image_url:
        #  Отправляем фото, если оно есть в базе данных
        context.bot.send_photo(update.message.chat_id, image_url, caption=cap)
        logging.info("Sent to @%s a Photo FIRST state.", update.message.from_user.first_name)
    else:
        #  Отправляем сооющение, если фото нет в базе данных
        context.bot.send_message(update.message.chat_id, text=cap)
        logging.info("Sent to @%s a Message FIRST state.", update.message.from_user.first_name)
    return ConversationHandler.END


def help(update, context):
    """Send info about Telegram bot"""
    logging.info("Sent to @%s a '/help' Message.", update.message.from_user.first_name)
    update.message.reply_text("Это Telegram Бот, который поможет тебе найти нужный рецепт,"
                              "узнать точное количество ингредиентов, которое понадобится для "
                              "определённого рецепта, а также познакомит тебя со способом "
                              "приготовления.\n"
                              "Как же им пользоваться?\n"
                              "Очень просто! Напишите боту /start и высветится главное меню с "
                              "10 разнообразными категориями. Выбрав нужную категорию, напишите в "
                              "чат номер нужного вам рецепта из появившегося списка.")


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            FIRST: [CallbackQueryHandler(one)],
            SECOND: [CallbackQueryHandler(start_over),
                     MessageHandler(Filters.text, get_receipt_number)]
        },
        fallbacks=[CommandHandler('start', start)]
    )
    )

    dp.add_error_handler(error)

    updater.start_polling()
    print('Принимаем сообщение')
    updater.idle()


if __name__ == '__main__':
    main()

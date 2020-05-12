from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, CommandHandler, \
    CallbackQueryHandler, ConversationHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Bot
import pyodbc as odbc
import time
from text_moderation import *
import logging

TOKEN = "1181461577:AAEGd2heqoKZfE0ZJHgnlhSXvRb8_hjIruw"
conn = odbc.connect(r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=db\CookingBook.mdb;')
cursor = conn.cursor()
cursor.execute('select * from Category')
categories = cursor.fetchall()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
data = []
# Stages
FIRST, SECOND = range(2)
# Callback data
ONE, TWO, THREE, FOUR = range(4)


def start(update, context):
    logger.info("User %s started the conversation.", update.message.from_user.first_name)
    keyboard = [[InlineKeyboardButton(row[1], callback_data=row[0])] for row in categories]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Выберите категорию рецептов:', reply_markup=reply_markup)
    return FIRST


def start_over(update, context):
    query = update.callback_query
    query.answer()
    logger.info("User %s restarted the conversation.", update.message.from_user.first_name)
    keyboard = [[InlineKeyboardButton(row[1], callback_data=row[0])] for row in categories]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text='Выберите категорию рецептов:', reply_markup=reply_markup)
    return FIRST


def one(update, context):
    query = update.callback_query
    query.answer()
    print('Получил ответ\t' + time.asctime())

    keyboard = [InlineKeyboardButton('Выбрать другую категорию', callback_data='1')]
    cursor.execute('select name from Book where id_category={}'.format(query.data))
    data = cursor.fetchall()
    text = 'Вот список блюд в категории {}'.format(categories[int(query.data)])
    for pos in range(len(data)):
        text = text + f'\n{pos}) {data[pos]}'
    text = text + f'\nНапишите в чат номер нужного рецепта'
    query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SECOND


def get_receipt_number(update, context):
    receipt = int(update.message.text)
    cursor.execute('select name, ingredients, cooking, photo from Book where name=?', data[receipt])
    name, ingredients, cooking, photo = cursor.fetchall()
    name, ingredients = format_name(name), format_ingredients(ingredients)
    cap = f"{name}\n" \
        f"СОСТАВ: {ingredients}" \
        f"Приготовление:{cooking}"
    update.edit_message_text(text='Приятного аппетита!!!', reply_markup=None)
    context.bot.send_photo(update.message.chat_id, photo, caption=cap)
    return ConversationHandler.END


def help(update, context):
    print('/help\t' + time.asctime())
    update.message.reply_text("Я пока не умею помогать... Я только ваше эхо.")


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

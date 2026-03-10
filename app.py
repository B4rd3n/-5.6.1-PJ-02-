import telebot
from telebot import types

from config import TOKEN
from extensions import APIException, CheckConversion
from redis_cache import AvailableCurrencies, FavoriteManager



bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = welcome_message()

    bot.send_message(message.chat.id, welcome_text, reply_markup = main_menu())


def welcome_message():
    welcome_text = ('Добро пожаловать!\n'
                    'Здесь вы можете посмотреть актуальные курсы валют.\n'
                    f'\nДоступно валют: {AvailableCurrencies.curr_amount()}')
    return welcome_text


def main_menu():
    markup = types.InlineKeyboardMarkup()

    help_btn = types.InlineKeyboardButton('❓Помощь', callback_data="help")
    value_btn = types.InlineKeyboardButton('💸 Доступные валюты', callback_data="value")
    favourite_btn = types.InlineKeyboardButton('⭐Избранные', callback_data="favourites")

    markup.add(help_btn, value_btn)
    markup.row(favourite_btn)

    return markup

def help_message():
    markup = types.InlineKeyboardMarkup()

    value_btn = types.InlineKeyboardButton('💸 Доступные валюты', callback_data="value")
    back_btn = types.InlineKeyboardButton('⬅️ Назад', callback_data="main_menu")

    markup.add(value_btn)
    markup.row(back_btn)

    return markup


def redact_favourite():
    markup = types.InlineKeyboardMarkup()

    add_fav = types.InlineKeyboardButton('➕ Добавить', callback_data = "add")
    remove_fav = types.InlineKeyboardButton('➖ Убрать', callback_data = "remove")
    show_fav = types.InlineKeyboardButton('📝 Список Избранного', callback_data = "show")
    back_btn = types.InlineKeyboardButton('⬅️ Назад', callback_data = "main_menu")

    markup.add(add_fav, remove_fav)
    markup.row(show_fav)
    markup.row(back_btn)


    return markup

def show_favourite_markup():

    markup = types.InlineKeyboardMarkup()

    back_btn = types.InlineKeyboardButton('⬅️ Назад', callback_data="main_menu")
    markup.row(back_btn)

    return markup


def process_add_favorite_step(message):

    user_id = message.from_user.id
    currency_code = message.text.upper()

    manager = FavoriteManager(user_id)
    result = manager.favorites(currency_code)

    bot.send_message(message.chat.id, result)


def process_remove_favorite_step(message):

    user_id = message.from_user.id
    currency_code = message.text.upper()

    manager = FavoriteManager(user_id)
    result = manager.remove_favorite(currency_code)

    bot.send_message(message.chat.id, result)


@bot.callback_query_handler(func=lambda call: call.data == "main_menu")
def main_menu_call(call):

    if call.data == "main_menu":
        welcome_text = welcome_message()

        bot.edit_message_text(welcome_text, call.message.chat.id, call.message.message_id, reply_markup = main_menu())



@bot.callback_query_handler(func=lambda call: call.data in ["help", "value", "favourites"])
def callback_menu_buttons(call):
    if call.data == "help":
        text = ("Для начала работы введите данные в следующем формате:\n"
                "<Конвертируемая валюта> <Желаемая валюта> <Количество>\n"
                "\n!ВАЖНО!\nДля ввода используйте коды валют (RUB, USD, AED и т.д.)")

        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup = help_message())

    if call.data == "value":

        with open("currencies.txt", "w", encoding='utf-8') as curr_list:
            curr_list.write(AvailableCurrencies.get_curr_txt())

        bot.send_message(call.message.chat.id, "Ознакомиться со списком доступных валют можно здесь: ")

        with open("currencies.txt", "rb") as f:

            bot.send_document(call.message.chat.id, f)

    if call.data == "favourites":
        text = ("Тут вы можете добавить, удалить любимую валюту, а также просмотреть список избранных."
                f"\n\nЛимит избранных валют: {FavoriteManager.max_limit} шт")

        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup = redact_favourite())



@bot.callback_query_handler(func=lambda call: call.data in ["add", "remove", "show"])
def favourites(call):


    if call.data == "add":
        add = bot.send_message(call.message.chat.id, "Введите код валюты для добавления (Например, USD): ")
        bot.register_next_step_handler(add, process_add_favorite_step)

    if call.data == "remove":
        remove = bot.send_message(call.message.chat.id, "Введите код валюты для удаления (Например, USD): ")
        bot.register_next_step_handler(remove, process_remove_favorite_step)

    if call.data == "show":
        user_id = call.from_user.id

        member = FavoriteManager(user_id)
        registered = member.show_favorite()
        text = f"Ваши избранные валюты:\n{registered}"

        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=show_favourite_markup(), parse_mode='HTML')




@bot.message_handler(content_types = ['text'])
def converter(message : telebot.types.Message):
    try:
        text = message.text.split(' ')

        if len(text) != 3:
            raise APIException("Неверное количество аргументов!")

        base, quote, amount = message.text.split(' ')
        base = base.upper()
        quote = quote.upper()

        convert = CheckConversion.final_price(base, quote, amount)

    except Exception as e:
        bot.send_message(message.chat.id, str(e))

    else:
        bot.send_message(message.chat.id, f"Итоговая цена: {round(convert, 2)} {quote}")


bot.polling(none_stop = True)




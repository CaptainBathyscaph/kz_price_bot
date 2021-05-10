import requests
import lxml
import config
import bd
import telebot
import datetime
from bs4 import BeautifulSoup as bs
from rfc3987 import parse
from keyboa import Keyboa
import schedule
import time
import threading


# инициализация бота
TOKEN = config.TOKEN
bot = telebot.TeleBot(config.TOKEN)

# обработка команды start
@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(
        message.chat.id,
        'Здравствуйте, данный бот предназначен для отслеживания цен интернет-товаров\n' +
        'Чтобы начать работу с ботом нужно добавить товар, для этого нажмите /add\n' +
        'Если нужна помощь нажмите /help'
    )
# обработка команды help
@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(
        message.chat.id,
        'Список команд: \n' +
        'Для добавления товара в отслеживание нажмите /add \n' +
        'Чтобы выбрать товар для проверки изменения цены нажмите /check \n' +
        'Для того, чтобы проверить все добавленные товары нажмите /auto \n')


# обработка команды add
@bot.message_handler(commands=['add'])
def add_command(message):
    bot.send_message(message.chat.id, 'Отправьте ссылку на товар. '+ 'ВНИМАНИЕ, на данный момент бот поддерживает только магазин Sulpak \n')
    bot.register_next_step_handler(message, add)

def add(message):
    url = message.text
    # проверка является ли сообщение ссылкой
    try:
        parse(url, rule='IRI')
    except ValueError:
        bot.send_message(message.chat.id, 'Неверная ссылка, нажмите /add чтобы повторить попытку')
        # если исключение с ошибкой, просим отправить еще раз
    else:
        #если исключение не возникло, парсим страницу
        html = requests.get(url).text
        soup = bs(html, "lxml")
        #парсим название товара
        title_original = soup.find(attrs={"class": "product-container-title"})
        name = title_original.text
        #если название слишком длинное делаем короче
        n = len(str(name).encode('utf-8'))
        if n >= 64:
            name = name[:48]
        #парсим текущую цену товара
        price_original = soup.find(attrs={"class": "current-price"})
        # из строки с ценой удаляем тг чтобы можно было перевести значение в число
        price = price_original.text.removesuffix("тг").replace(" ", "")
        user_id = message.from_user.id
        date = datetime.datetime.now()
        # проверяем нет ли уже товара в бд
        if (not bd.SQLlighter.item_exist(name, user_id)):
            bd.SQLlighter.add_bd(user_id, date, name, price, url)
            # если нет добавляем информацию в бд и отправляем пользователю сообщение о добавлении
            bot.send_message(message.chat.id, 'Товар добавлен в базу данных')
        else:
            #bd.SQLlighter.update_price(date, price, name)
            price_bd = bd.SQLlighter.get_price(name)
            price_bd = int(price_bd[0])
            url = "".join(map(','.join, url))
            html = requests.get(url).text
            soup = bs(html, "lxml")
            price_original = soup.find(attrs={"class": "current-price"})
            price_current = price_original.text.removesuffix("тг").replace(" ", "")
            price_current = int(price_current)
            user_id = message.from_user.id
            date = datetime.datetime.now()
            if price_current == price_bd:
                bot.send_message(message.chat.id, 'Товар с данной ценной уже есть в базе данных')
            else:
                if price_current > price_bd:

                    bot.send_message(message.chat.id, 'Цена на товар: ' + name + ' увеличилась на ' + str(
                        price_current - price_bd) + ' тг. Новая цена: ' + str(price_current) + ' тг. \n')
                    bd.SQLlighter.add_bd(user_id, date, name, price_current, url)
                    bot.send_message(message.chat.id, 'Новая цена сохранена \n')
                else:
                    bot.send_message(message.chat.id, 'Цена на товар:  ' + name + ' уменьшилась на ' + str(
                        price_bd - price_current) + ' тг. Новая цена: ' + str(price_current) + ' тг. \n')
                    bd.SQLlighter.add_bd(user_id, date, name, price_current, url)
                    bot.send_message(message.chat.id, 'Новая цена сохранена \n')


# обработка команды check
@bot.message_handler(commands=['check'])
def check_command(message1):
    names = bd.SQLlighter.get_name(message1.from_user.id)
    names_list = [item for sub in names for item in sub]
    keyboard = Keyboa(items=names_list, copy_text_to_callback=True).keyboard
    bot.send_message(message1.chat.id, reply_markup=keyboard, text="Выберите товар для проверки \n")

    @bot.callback_query_handler(func=lambda call: True)
    def callback(call):
        choice(call)

def choice(message2):
    name = message2.data
    url_bd = bd.SQLlighter.get_url(name)
    price_bd = bd.SQLlighter.get_price(name)
    price_bd = int(price_bd[0])
    url = "".join(map(','.join,url_bd))
    html = requests.get(url).text
    soup = bs(html, "lxml")
    price_original = soup.find(attrs={"class": "current-price"})
    price_current = price_original.text.removesuffix("тг").replace(" ", "")
    price_current = int(price_current)
    user_id = message2.message.from_user.id
    date = datetime.datetime.now()
    if price_current == price_bd:
        bot.send_message(message2.message.chat.id, 'Цена на товар:  '+ name + ' не изменилась \n')
    else:
        if price_current > price_bd:

            bot.send_message(message2.message.chat.id, 'Цена на товар: '+ name + ' увеличилась на ' + str(price_current-price_bd)  +  ' тг. Новая цена: ' + str(price_current) + ' тг. \n' )
            bd.SQLlighter.add_bd(user_id, date, name, price_current, url)
            bot.send_message(message2.message.chat.id, 'Новая цена сохранена \n')
        else:
            bot.send_message(message2.message.chat.id, 'Цена на товар:  ' + name + ' уменьшилась на ' + str(price_bd - price_current) + ' тг. Новая цена: ' + str( price_current) + ' тг. \n')
            bd.SQLlighter.add_bd(user_id, date, name, price_current, url)
            bot.send_message(message2.message.chat.id, 'Новая цена сохранена \n')


@bot.message_handler(commands=['history'])
def history(message1):
    names = bd.SQLlighter.get_name(message1.from_user.id)
    names_list = [item for sub in names for item in sub]
    keyboard = Keyboa(items=names_list, copy_text_to_callback=True).keyboard
    bot.send_message(message1.chat.id, reply_markup=keyboard, text="Выберите товар для проверки \n")

@bot.callback_query_handler(func=lambda call: True)
def history_callback(call):
    choice2(call)

def choice2(callback):
    name = callback.data
    price_history, date_history = bd.SQLlighter.get_price_history(name)
    user_id = callback.from_user.id
    price_history = [item for sub in price_history for item in sub]
    date_history = [item for sub in date_history for item in sub]
    #list = [item for sub in price_history for item in sub]
    for i in range(len(price_history)):
        t = date_history[i]
        #s = t.strftime('%Y-%m-%d %H:%M:%S.%f')
        bot.send_message(user_id, "Дата: " + t[:-7] + " Цена: " + str(price_history[i]) + ' \n')


 # обработка команды check
@bot.message_handler(commands=['auto'])
def auto_check_message(message):
        names = bd.SQLlighter.get_name(message.from_user.id)
        names_list = [item for sub in names for item in sub]
        for i in names_list:
            name = i
            url_bd = bd.SQLlighter.get_url(name)
            price_bd = bd.SQLlighter.get_price(name)
            price_bd = int(price_bd[0])
            url = "".join(map(','.join, url_bd))
            html = requests.get(url).text
            soup = bs(html, "lxml")
            price_original = soup.find(attrs={"class": "current-price"})
            price_current = price_original.text.removesuffix("тг").replace(" ", "")
            price_current = int(price_current)
            user_id = message.from_user.id
            date = datetime.datetime.now()
            if price_current == price_bd:
                bot.send_message(message.chat.id, 'Цена на товар: '+ name + ' не изменилась \n')
            else:
                if price_current > price_bd:
                    bot.send_message(message.chat.id,
                                 'Цена на товар: '+ name + ' увеличилась на ' + str(price_current - price_bd) + ' тг. Новая цена: ' + str(
                                     price_current) + ' тг. \n')
                    bd.SQLlighter.add_bd(user_id, date, name, price_current, url)
                    bot.send_message(message.chat.id, 'Новая цена сохранена \n')
                else:
                    bot.send_message(message.chat.id,
                                 'Цена на товар: '+ name + ' уменьшилась на ' + str(price_bd - price_current) + ' тг. Новая цена: ' + str(
                                     price_current) + ' тг. \n')
                    bd.SQLlighter.add_bd(user_id, date, name, price_current, url)
                    bot.send_message(message.chat.id, 'Новая цена сохранена \n')


def auto_check_id(user_id):
    names = bd.SQLlighter.get_name(user_id)
    names_list = [item for subj in names for item in subj]
    for i in names_list:
        name = i
        url_bd = bd.SQLlighter.get_url(name)
        price_bd = bd.SQLlighter.get_price(name)
        price_bd = int(price_bd[0])
        url = "".join(map(','.join, url_bd))
        html = requests.get(url).text
        soup = bs(html, "lxml")
        price_original = soup.find(attrs={"class": "current-price"})
        price_current = price_original.text.removesuffix("тг").replace(" ", "")
        price_current = int(price_current)
        date = datetime.datetime.now()
        if price_current == price_bd:
            pass
        else:
            if price_current > price_bd:
                bot.send_message(user_id,
                                 'Цена на товар: ' + name + ' увеличилась на ' + str(
                                     price_current - price_bd) + ' тг. Новая цена: ' + str(
                                     price_current) + ' тг. \n')
                bd.SQLlighter.add_bd(user_id, date, name, price_current, url)
                bot.send_message(user_id, 'Новая цена сохранена \n')
            else:
                bot.send_message(user_id,
                                 'Цена на товар: ' + name + ' уменьшилась на ' + str(
                                     price_bd - price_current) + ' тг. Новая цена: ' + str(
                                     price_current) + ' тг. \n')
                bd.SQLlighter.add_bd(user_id, date, name, price_current, url)
                bot.send_message(user_id, 'Новая цена сохранена \n')

def everyday_check():
    sub = bd.SQLlighter.get_subscriptions()
    sub_list = [item for subj in sub for item in subj]
    for i in sub_list:
        auto_check_id(i)

schedule.every().day.at("12:00").do(everyday_check)
def go():
    while 1:
        schedule.run_pending()
        time.sleep(3600)

t = threading.Thread(target=go, name="тест")
t.start()

bot.polling(none_stop=True, interval=0)
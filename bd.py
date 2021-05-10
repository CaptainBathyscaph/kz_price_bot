import sqlite3


class SQLlighter:
    """Добавляем инфу в бд"""
    def add_bd(user_id, date, name, price, url):
        connection = sqlite3.connect('db.db')
        cursor = connection.cursor()
        cursor.execute("INSERT INTO `prices` (`user_id`, `date`, 'name', 'price', 'url') VALUES(?,?,?,?,?)", (user_id, date, name, price, url))
        connection.commit()

        #проверка на наличие товара в бд
    def item_exist(name, user_id):
        connection = sqlite3.connect('db.db')
        cursor = connection.cursor()
        result = cursor.execute('SELECT * FROM `prices` WHERE `name` = ?  AND "user_id" = ? ORDER BY date DESC LIMIT 1', (name, user_id)).fetchall()
        connection.commit()
        return bool(len(result))

    def get_subscriptions():
        connection = sqlite3.connect('db.db')
        cursor = connection.cursor()
        sub = cursor.execute('SELECT DISTINCT user_id FROM `prices`').fetchall()
        return sub


    def get_url(name):
        connection = sqlite3.connect('db.db')
        cursor = connection.cursor()
        url = cursor.execute('SELECT url FROM `prices` WHERE `name` = ? ORDER BY date DESC LIMIT 1', (name, )).fetchall()
        return url

    def get_name(user_id):
        connection = sqlite3.connect('db.db')
        cursor = connection.cursor()
        name = cursor.execute('SELECT DISTINCT name FROM `prices` WHERE `user_id` = ?', (user_id, )).fetchall()
        return name

    def get_price(name):
        connection = sqlite3.connect('db.db')
        cursor = connection.cursor()
        bd_price = cursor.execute('SELECT price FROM `prices` WHERE `name` = ? ORDER BY date DESC LIMIT 1', (name,)).fetchone()
        cursor.close()
        return bd_price

    def get_price_history(name):
        connection = sqlite3.connect('db.db')
        cursor = connection.cursor()
        date_history = cursor.execute('SELECT date FROM `prices` WHERE `name` = ? ', (name,)).fetchall()
        price_history = cursor.execute('SELECT price FROM `prices` WHERE `name` = ? ', (name, )).fetchall()
        return price_history, date_history


    def update_price(date, price, name):
        #обновляем дату и цену
        connection = sqlite3.connect('db.db')
        cursor = connection.cursor()
        cursor.execute('UPDATE `prices` SET `date` = ?, `price` = ?  WHERE `name` = ?', (date, price, name))
        connection.commit()
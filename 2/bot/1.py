import logging
import mysql.connector
from mysql.connector import Error
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from datetime import datetime
from mysql.connector import IntegrityError
# Устанавливаем уровень логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
def connect():
    # Получаем данные для подключения к БД
    db_config = {
        'host': '127.0.0.1',
        'user': 'admin',
        'password': 'a9p6bc36vyxxSuJs',
        'database': 'kulig_bd',
    }

    # Создаем подключение к БД
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            print('Connected to MySQL database')
        return connection
    except Error as e:
        print('Error:', e)
        return {'Error:', e}

# Словарь для хранения пользователей
users = {}

# Словарь для временного хранения данных пользователя
user_temp_data = {}

# Команда /start
def start(update: Update, context: CallbackContext) -> None:
    connection = connect()
    user_id = update.message.from_user.id

    # Проверяем, зарегистрирован ли пользователь
    if user_id in users:
        update.message.reply_text(f'Здравствуйте, {users[user_id]["first_name"]}!')
    else:
        cursor = connection.cursor()
        query = "SELECT C_Name FROM profile WHERE C_ID = %s"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()

        if result:
            user_name = result[0]
            update.message.reply_text(f'Здравствуйте, {user_name}! \nчтобы узнать свой баланс нажмите /balance\nчтобы выбрать тариф нажмите /hostingplan\nуже преобретённые тарифы /myplans  ')
        else:
            users[user_id] = {
                'id': user_id,
                'first_name': '',
                'last_name': '',
                'phone': '',
                'email': '',
                'username': update.message.from_user.username,
            }

            # Запрашиваем имя пользователя
            update.message.reply_text('Пожалуйста, введите ваше имя:')
            context.user_data['current_step'] = 'get_name'
# Обработка текстовых сообщений
def handle_text(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    current_step = context.user_data.get('current_step', None)

    if current_step == 'get_name':
        users[user_id]['first_name'] = update.message.text
        # Запрашиваем фамилию пользователя
        update.message.reply_text('Теперь введите вашу фамилию:')
        context.user_data['current_step'] = 'get_last_name'

    elif current_step == 'get_last_name':
        users[user_id]['last_name'] = update.message.text
        # Запрашиваем номер телефона пользователя
        update.message.reply_text('Теперь введите ваш номер телефона:')
        context.user_data['current_step'] = 'get_phone'

    elif current_step == 'get_phone':
        users[user_id]['phone'] = update.message.text
        # Запрашиваем email пользователя
        update.message.reply_text('Теперь введите ваш email:')
        context.user_data['current_step'] = 'get_email'

    elif current_step == 'get_email':
        users[user_id]['email'] = update.message.text
        # Добавляем пользователя в базу данных
        add_user_to_db(users[user_id])
        update.message.reply_text('Спасибо! Вы успешно зарегистрированы.')

# Функция для добавления пользователя в БД
def add_user_to_db(user):
    connection= connect()
    try:
        cursor = connection.cursor()

        # Проверяем, зарегистрирован ли пользователь
        query = "SELECT C_ID FROM profile WHERE C_ID = %s"
        cursor.execute(query, (user['id'],))
        result = cursor.fetchone()

        if result:
            # Если пользователь уже зарегистрирован, отправляем ему сообщение
            global_updater.bot.send_message(chat_id=user['id'], text='Вы уже зарегистрированы.')
        else:
            # Ваш запрос для добавления пользователя в таблицу profile
            query = "INSERT INTO profile (C_ID, C_Name, C_Surname, C_Email, C_Phone, C_Balance, TG_ID) " \
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)"
            values = (user['id'], user['first_name'], user['last_name'], user['email'], user['phone'], 0, None)

            cursor.execute(query, values)
            connection.commit()
            global_updater.bot.send_message(chat_id=user['id'], text='Спасибо! Вы успешно зарегистрированы.')

    except Error as e:
        print('Error:', e)
# Команда /balance
def balance(update: Update, context: CallbackContext) -> None:
    connection=connect()
    user_id = update.message.from_user.id
    
    cursor = connection.cursor()

    # Проверяем, зарегистрирован ли пользователь
    query = "SELECT C_Balance FROM profile WHERE C_ID = %s"
    cursor.execute(query, (user_id,))
    result = cursor.fetchone()

    if result:
        user_balance = result[0]
        update.message.reply_text(f'Ваш текущий баланс: {user_balance} руб.')
    else:
        update.message.reply_text('Вы не зарегистрированы. Используйте команду /start для регистрации.')

    # Обновляем данные в контексте
    context.user_data['current_balance'] = user_balance
    
    
# Команда /hostingplan
def hosting_plan(update: Update, context: CallbackContext) -> None:
    connection = connect()
    user_id = update.message.from_user.id

    # Проверяем, зарегистрирован ли пользователь
    cursor = connection.cursor()
    query = "SELECT C_ID FROM profile WHERE C_ID = %s"
    cursor.execute(query, (user_id,))
    result = cursor.fetchone()

    if result:
        # Пользователь зарегистрирован
        keyboard = []
        query = "SELECT HP_ID, HP_Name, HP_Price FROM hostingplans"
        cursor.execute(query)
        hosting_plans = cursor.fetchall()

        if hosting_plans:
            for plan in hosting_plans:
                keyboard.append([InlineKeyboardButton(f"{plan[1]} - ${plan[2]}", callback_data=str(plan[0]))])

            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text("Выберите хостинг план:", reply_markup=reply_markup)
            context.user_data['current_step'] = 'choose_hosting_plan'
        else:
            update.message.reply_text("Нет доступных хостинг планов.")
    else:
        update.message.reply_text('Вы не зарегистрированы. Используйте команду /start для регистрации.')

    cursor.close()
    connection.close()


# Обработка выбора хостинг плана
def choose_hosting_plan(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    plan_id = int(query.data)
    user_id = query.from_user.id

    # Создаем новый заказ
    create_new_order(user_id, plan_id)

    query.edit_message_text(f"Вы выбрали хостинг план с ID {plan_id}.")

# Функция для создания нового заказа
def create_new_order(user_id, plan_id):
    connection = connect()
    cursor = connection.cursor()

    try:
        # Проверяем, что пользователь уже зарегистрирован
        query = "SELECT * FROM profile WHERE C_ID = %s"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()

        if result:
            # Проверяем, что хостинг план существует
            query = "SELECT * FROM hostingplans WHERE HP_ID = %s"
            cursor.execute(query, (plan_id,))
            plan_result = cursor.fetchone()

            if plan_result:
                # Проверяем, не существует ли уже заказ с таким хостинг планом
                query = "SELECT * FROM orders WHERE HP_ID = %s"
                cursor.execute(query, (plan_id,))
                existing_order = cursor.fetchone()
                if existing_order:
                    chek= existing_order[1]

                if not existing_order or chek != user_id:
                    # Получаем текущую дату
                    current_date = datetime.now().strftime('%Y-%m-%d')
                    # Получаем баланс пользователя
                    user_balance = result[5]  # Индекс 5 соответствует C_Balance в таблице profile

                    # Получаем стоимость хостинг плана
                    plan_price = plan_result[1]  # Индекс 1 соответствует HP_Price в таблице hostingplans

                    # Проверяем, хватает ли у пользователя средств для заказа
                    if user_balance >= plan_price:                    
                        # Создаем новый заказ
                        query = "INSERT INTO orders (HP_ID, C_ID, O_Status, P_Date) VALUES (%s, %s, %s, %s)"
                        values = (plan_id, user_id, 1, current_date)
                        cursor.execute(query, values)
                        connection.commit()
                        global_updater.bot.send_message(chat_id=user_id, text='Заказ успешно создан!')
                    else:
                        global_updater.bot.send_message(chat_id=user_id, text='Недостаточно средств для заказа.')                
                else:
                    global_updater.bot.send_message(chat_id=user_id, text='У вас уже есть заказ с этим хостинг планом.')
            else:
                global_updater.bot.send_message(chat_id=user_id, text='Выбранный хостинг план не существует.')
        else:
            global_updater.bot.send_message(chat_id=user_id, text='Вы не зарегистрированы. Используйте команду /start для регистрации.')
    except Error as e:
        print('Error:', e)
    finally:
        cursor.close()
        connection.close()
        
# Команда /myplans
def my_plans(update: Update, context: CallbackContext) -> None:
    connection = connect()
    user_id = update.message.from_user.id

    # Проверяем, зарегистрирован ли пользователь
    cursor = connection.cursor()
    query = "SELECT * FROM profile WHERE C_ID = %s"
    cursor.execute(query, (user_id,))
    result = cursor.fetchone()

    if result:
        # Пользователь зарегистрирован, получаем информацию о его хостинг-планах
        query = """
            SELECT h.HP_Name, h.HP_Price
            FROM hostingplans h
            JOIN orders o ON h.HP_ID = o.HP_ID
            WHERE o.C_ID = %s
        """
        cursor.execute(query, (user_id,))
        user_plans = cursor.fetchall()

        if user_plans:
            message = "Ваши приобретённые хостинг-планы:\n"
            for plan in user_plans:
                message += f"{plan[0]} - ${plan[1]}\n"

            update.message.reply_text(message)
        else:
            update.message.reply_text("Вы ещё не приобрели ни одного хостинг-плана.")
    else:
        update.message.reply_text('Вы не зарегистрированы. Используйте команду /start для регистрации.')

    cursor.close()
    connection.close()
    
# Основная функция
def main() -> None:
    global global_updater
    # Создаем Updater и передаем ему токен бота
    updater = Updater('6937014856:AAGVGiVGNuFCCarRfgXynYjR8Uxe7jCpuGU')
    global_updater = updater  # Сохраняем updater в глобальной переменной

    # Получаем диспетчер от updater
    dp = updater.dispatcher
    # Добавляем обработчик команды /hostingplan
    dp.add_handler(CommandHandler("hostingplan", hosting_plan))

    # Добавляем обработчик выбора хостинг плана
    dp.add_handler(CallbackQueryHandler(choose_hosting_plan))
    # Добавляем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("balance", balance))  # Добавляем обработчик команды /balance
    # Добавляем обработчик команды /myplans
    dp.add_handler(CommandHandler("myplans", my_plans))

    # Добавляем обработчик текстовых сообщений
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))

    # Запускаем бота
    updater.start_polling()

    # Останавливаем бота при нажатии Ctrl+C
    updater.idle()

if __name__ == '__main__':
    main()

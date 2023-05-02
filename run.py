import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from google_module.google_module import put_values
import json
from aiogram.exceptions import AiogramError, TelegramForbiddenError
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
import send_files

# Статусы сообщений
statuses = {}


# Чтение конфига
with open("config.json", "r") as read_file:
    config = json.load(read_file)

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# root_logger= logging.getLogger()
# root_logger.setLevel(logging.WARNING) # or whatever
# handler = logging.FileHandler('app.log', 'a', 'utf-8') # or whatever
# handler.setFormatter(logging.Formatter('%(name)s %(message)s - %(asctime)s')) # or whatever
# root_logger.addHandler(handler)

# Объект бота
bot = Bot(token=config["TG_TOKEN"])
# Диспетчер
dp = Dispatcher()


@dp.callback_query(lambda call: call.from_user.id not in statuses)
async def start_callback(call: types.CallbackQuery):
    """
    Обработка нажатия inline кнопки, пока пользователь не начал работу с ботом
    """
    try:
        await call.message.delete()
    except:
        return await call.message.answer("Возникла ошибка. Введите заново /start для прохождения тестирования")
    await cmd_start(call.message)


@dp.message(commands=["instructions"])
async def inst_start(message: types.Message):
    """
    На команду /instructions высылаем инструкции
    """
    return await sending_messages("""Перед заполнением документа просим ознакомится с правилами заполнения:
1. Задачи будут выполняться по мере их поступления с учетом приоритета и срочности (а также сочности 😉).
2. Необходимо корректно и наиболее подробно формулировать запрос (просто если будет не очень понятно, то мы начнем писать и так далее… ну Вы поняли😵‍💫).
3. Приоритет не игрушка 🧸 Оценивайте его адекватно. Где 1 - Не приоритетно, 10 - Очень приоритетно.
4. По желанию Вы можете указать себя как автора. (Мы вам благодарность напишем).
5. В запрос можно написать свою идею, недоработку или неэффективность, которую Вы заметили, трудности с которыми столкнулись и они снизили вашу эффективность.
6. Вводите сроки в формате дата.месяц
7. Ответственный за реестр - <a href="https://t.me/">Name</a>.""", message=message, parse_mode="HTML")


# Хэндлер на команду /start
@dp.message(lambda message: message.from_user.id not in statuses)
@dp.message(commands=["start"])
async def cmd_start(message: types.Message):
    """
    Обработка команды /start либо ввода текста, пока работа с ботом не началась
    """
    # Если не в личку написали, то игнорим
    if message.from_user.id != message.chat.id:
        return
    # Записывем в словарь пустой список, который будем заполнять позже
    statuses[message.from_user.id] = []
    await sending_messages("""Приветствую! Этот бот создан для того, чтобы Вы могли анонимно поделиться:
-трудностью, с которой постоянно сталкиваетесь;
-предложением по улучшению работы;
-гипотезой/мыслью, которую хотите проверить;
-задачи, до которых не доходят руки и не хватает времени.

Советуем ознакомиться с <b>регламентом</b> /instructions
Чтобы начать опрос заново, введите /start (его можно найти в меню)""", message=message, parse_mode="HTML", reply_markup=types.ReplyKeyboardRemove())

    # Генерируем клавиатуру с отделами
    builder = InlineKeyboardBuilder()
    
    builder.row(
        types.InlineKeyboardButton(text="Маркетинг", callback_data="Маркетинг"), 
        types.InlineKeyboardButton(text="Снабжение", callback_data="Снабжение")
    )
    builder.row( 
        types.InlineKeyboardButton(text="Логистика", callback_data="Логистика"), 
        types.InlineKeyboardButton(text="Админ. отдел", callback_data="Админ. отдел")
    )
    builder.row(
        types.InlineKeyboardButton(text="Отдел Развития", callback_data="Отдел Развития"), 
        types.InlineKeyboardButton(text="", callback_data="") 
    )
    builder.row(
        types.InlineKeyboardButton(text="", callback_data=""), 
        types.InlineKeyboardButton(text="", callback_data="")
    )
    builder.row(
        types.InlineKeyboardButton(text="HR", callback_data="HR"), 
        types.InlineKeyboardButton(text="Бухгалтерия", callback_data="Бухгалтерия")
    )
    builder.row( 
        types.InlineKeyboardButton(text="Среда Развития", callback_data="Среда Развития"), 
        types.InlineKeyboardButton(text="Внутрянка", callback_data="Внутрянка") 
    )

    return await sending_messages("Укажите отдел, от которого исходит ваш запрос:", message=message , reply_markup=builder.as_markup())


@dp.callback_query(lambda call: call.from_user.id in statuses and len(statuses[call.from_user.id]) == 0)
async def getting_advice(call: types.CallbackQuery):
    """
    Обрабатываем получение отдела (нажатие по оному выше). Высылаем просьбу отправить идею
    """
    # Добавляем отдел
    statuses[call.from_user.id].append(call.data)
    # Удаляем сообщение, чтобы кнопки пропали
    try:
        await call.message.delete()
    except:
        pass
    await sending_messages(
        "Опишите свой запрос, идею или предложение. Расписывайте ее максимально понятно с указанием ссылок и подробным описанием того, что необходимо сделать (поэтапно).\n<b>Вышлите сначала предложения, а в следующем сообщении - файлы</b>",
         message=call.message, parse_mode="HTML"
    )


@dp.message(lambda message: message.from_user.id in statuses and (len(statuses[message.from_user.id]) == 1 or len(statuses[message.from_user.id]) == 2))
async def getting_priority(message: types.Message):
    """
    Обрабатываем получение идеи. Предлагаем после отправить документы
    """
    builder = InlineKeyboardBuilder()
    # Если захочет окончить отправку файлов
    builder.row(
        types.InlineKeyboardButton(text="У меня всё!", callback_data="всё")
    )
    # Если пока идею не получали
    if len(statuses[message.from_user.id]) == 1:
        # А пользователь уже шлёт файлы
        if not message.text:
            return await sending_messages("Сначала пришлите текст, а после - документы", message=message)
        # Заменяем символы, чтобы html parse_mode нормально работал
        text = message.text
        text = text.replace("&","&amp;")
        text = text.replace("<","&lt;")
        text = text.replace(">","&gt;")
        # Добавляе словавь, в который будем дописывать id файлов, что вышлет пользователь
        statuses[message.from_user.id].append({"text":text, "photo":[], "document":[], "video":[], "audio":[]})

        return await sending_messages("Если есть вложения — можете их скинуть сюда.\nКак закончите нажимайте на эту кнопку👇", reply_markup=builder.as_markup(), message=message)

    # Если вложение не фото/видео/док/аудио, то не принимаем
    if not message.photo and not message.video and not message.document and not message.audio:
        return await sending_messages("Вложение не принято. Пришлите только фото/видео/документ/аудио", reply_markup=builder.as_markup(), message=message)
    # Запоминаем id файлов
    if message.photo:
        statuses[message.from_user.id][-1]["photo"].append(types.input_media_photo.InputMediaPhoto(media=message.photo[-1].file_id))
    elif message.video:
        statuses[message.from_user.id][-1]["video"].append(types.input_media_video.InputMediaVideo(media=message.video.file_id))
    elif message.document:
        statuses[message.from_user.id][-1]["document"].append(types.input_media_document.InputMediaDocument(media=message.document.file_id))
    elif message.audio:
        statuses[message.from_user.id][-1]["audio"].append(types.input_media_audio.InputMediaAudio(media=message.audio.file_id))
    elif message.text:
        return await sending_messages("Вы уже выслали текст. Теперь вышлите вложения", reply_markup=builder.as_markup(), message=message)

    return await sending_messages("Вложение принято. Если у Вас есть ещё, можете присылать. Как только закончите, нажмите по кнопке ниже👇", reply_markup=builder.as_markup(), message=message)


@dp.callback_query(lambda call: call.data=="всё" and call.from_user.id in statuses and len(statuses[call.from_user.id]) == 2)
async def getting_files(call: types.CallbackQuery):
    """
    Идеи закончились, пользователь нажал на кнопку У меня всё. Теперь просим указать приоритет
    """
    # Добавим None чтобы по длине списка было ясно, что с идеями всё
    statuses[call.from_user.id].append(None)
    # Клавиатура
    kb = [
        [types.KeyboardButton(text=str(i)) for i in range(1,6)],
        [types.KeyboardButton(text=str(i)) for i in range(6,11)]
    ]
    
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)
    return await sending_messages("Укажите приоритет. Где 1 - Не приоритетно, 10 - Очень приоритетно.", message=call.message, reply_markup=keyboard)


@dp.message(lambda message: message.from_user.id in statuses and len(statuses[message.from_user.id]) == 3)
async def getting_urgency(message: types.Message):
    """
    Получаем приоритет. Просим указать сроки
    """
    # Проверка на корректные данные
    if message.text not in "12345678910":
        kb = [
            [types.KeyboardButton(text=str(i)) for i in range(1,6)],
            [types.KeyboardButton(text=str(i)) for i in range(6,11)]
        ]
        keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)
    
        return await sending_messages("Укажите приоритет. Где 1 - Не приоритетно, 10 - Очень приоритетно", message=message, reply_markup=keyboard)
    
    # Добавляем приоритет
    statuses[message.from_user.id].append(message.text)
    return await sending_messages("Есть конкретный срок у задачи?\nЕсли да — то укажите его в формате \"дд.мм\". Если нет — то напишите \"нет\"", message=message, reply_markup=types.ReplyKeyboardRemove())
    

@dp.message(lambda message: message.from_user.id in statuses and len(statuses[message.from_user.id]) == 4)
async def getting_anonymous(message: types.Message):
    """
    Получаем сроки. Просим указать анонимность
    """
    # Добавляем срочность
    statuses[message.from_user.id].append(message.text)
    
    kb = [
        [types.KeyboardButton(text="Анонимно")],[types.KeyboardButton(text="Указав имя")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)
    return await sending_messages("Вы желаете отправить запрос анонимно или указав имя?", message=message, reply_markup=keyboard)


@dp.message(lambda message: message.from_user.id in statuses and len(statuses[message.from_user.id]) == 5)
async def getting_name(message: types.Message):
    """
    Получаем анонимность, финиш/полуаем имя
    """
    # Проверка корректных значений
    if message.text not in ["Указав имя", "Анонимно"]:
        kb = [
            [types.KeyboardButton(text="Анонимно")],[types.KeyboardButton(text="Указав имя")]
        ]
        keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)
        return await sending_messages("Вы желаете отправить запрос анонимно или указав имя?", message=message, reply_markup=keyboard)
    
    # Добавляем анонимность
    statuses[message.from_user.id].append(message.text)
    # Если выбрал анонимность, то всё
    if message.text == "Анонимно":
        await sending_messages(f"Спасибо за оставленную заявку!😉\nМы постараемся реализовать задание как можно скорее. При необходимости в ближайшее время с вами свяжется исполнитель и обговорит детали.\n<b>Чтобы пройти тест заново</b>, нажмите на /start\n<b>Ознакомиться с регламентом</b> /instructions", message=message, reply_markup=types.ReplyKeyboardRemove(), parse_mode="HTML")
        await sending_messages('<b>Ответственный за реестр</b> - <a href="https://t.me/">Name</a>\nЕсли остались вопросы, предложения или желание пообщаться — обращайтесь к нему👌', message=message, parse_mode="HTML")
        
        ### Пушим в таблицу
        await put_values(config["URL_FOR_TABLE"], statuses[message.from_user.id] + [message.from_user.username])
        
        # Что б проще обращаться было, в "a" запомним список из словаря
        a = statuses[message.from_user.id]

        # Получаем никнейм
        username = f"\n\n<b>Юзер-тег автора:</b> @{message.from_user.username}" if message.from_user.username else ""
        # Оповещение в тг чат
        message_id = await sending_messages(f"В реестре предложений появился новый запрос от \n<b>{a[0]}</b>\n\n<b>Текст:</b> {a[1]['text'] if len(a[1]['text'])<3000 else a[1]['text'][:3000]}\n\n<b>Приоритет -</b> {a[3]}\n<b>Дата -</b> {a[4]}{username}", id=config["CHAT_ID"], parse_mode="HTML")

        # Отправляем файлы, что были высланы с идеями
        await send_files.send_data(bot, a[1], config["CHAT_ID"], message_id, config) 
        
        # Чистим словарь
        del statuses[message.from_user.id]
        return
    else:
        return await sending_messages("Укажите ваше имя", message=message, reply_markup=types.ReplyKeyboardRemove())


@dp.message(lambda message: message.from_user.id in statuses and len(statuses[message.from_user.id]) == 6)
async def the_end(message: types.Message):
    """
    Получаем имя, финиш
    """
    # Добавляем имя
    statuses[message.from_user.id].append(message.text)

    await sending_messages(f"Спасибо за оставленную заявку!😉\nМы постараемся реализовать задание как можно скорее. При необходимости в ближайшее время с вами свяжется исполнитель и обговорит детали.\n<b>Чтобы пройти тест заново</b>, нажмите на /start\n<b>Ознакомиться с регламентом</b> /instructions", message=message, reply_markup=types.ReplyKeyboardRemove(), parse_mode="HTML")
    await sending_messages('Ответственный за реестр - <a href="https://t.me/">Name</a>\nЕсли остались вопросы, предложения или желание пообщаться — обращайтесь к нему👌.', message=message, parse_mode="HTML")

    # Удаляем Анонимно/Не анонимно    
    del statuses[message.from_user.id][-2]
    
    # Пушим в таблицу
    await put_values(config["URL_FOR_TABLE"], statuses[message.from_user.id] + [message.from_user.username])

    # Что б проще обращаться было, в "a" запомним список из словаря
    a = statuses[message.from_user.id]

    # Получаем никнейм
    username = f"\n\n<b>Юзер-тег автора:</b> @{message.from_user.username}" if message.from_user.username else ""
    # Оповещение в чат
    message_id = await sending_messages(f"В реестре предложений появился новый запрос от \n<b>{a[0]}</b>\n\n<b>Текст:</b> {a[1]['text'] if len(a[1]['text'])<3000 else a[1]['text'][:3000]}\n\n<b>Приоритет -</b> {a[3]}\n<b>Дата -</b> {a[4]}\n<b>Автор -</b> {a[-1]}{username}", id=config["CHAT_ID"], parse_mode="HTML")

    # Отправляем файлы, что были высланы с идеями
    await send_files.send_data(bot, a[1], config["CHAT_ID"], message_id, config) 
    
    # Чистим словарь
    del statuses[message.from_user.id]
    return


# Запуск процесса поллинга новых апдейтов
async def main():
    while True:
        try:
            await dp.start_polling(bot)
        except:
            await asyncio.sleep(5)


# Если вдруг ошибки, что б сообщение точно отправилось
# Может остановить поток
async def sending_messages(text, id=None, message=None, reply_markup=None, parse_mode=None):
    """
    Отправка сообщений в тг. У заказчика не очень интернет, из-за этого так делаю
    Возвращаем id отправленного сообщения
    """
    while True:
        try:
            if message:             # Если отвечаем на сообщение
                answer = await message.answer(text, parse_mode=parse_mode, reply_markup=reply_markup)
            else:                   # Если отправляем сообщение
                answer = await bot.send_message(id, text, parse_mode=parse_mode, reply_markup=reply_markup)
            # Возвращаем id отправленного сообщения
            return answer.message_id
        except TelegramForbiddenError as e:
            logging.warning(e)
            break
        except AiogramError as e:
            logging.warning(e)
            await asyncio.sleep(2)


if __name__ == "__main__":
    # Запуск тг бота
    asyncio.run(main())

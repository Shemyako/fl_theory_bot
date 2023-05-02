from aiogram import Bot, Dispatcher, types
import asyncio
from aiogram.exceptions import AiogramError, TelegramForbiddenError

async def send_data(bot, data, chat_id, message_id, config):
    """
    Высылаем файлы. Сложность - если файл один, то в тг одна функция за это отвечает. Если несколько, то другая
    bot - объект бота. Через него будет высылка данных
    data - словарь со списками с id файлов
    chat_id - id чата, куда слать файлы
    message_id - id сообщения с идеей, чтобы на него отвечать файлами (чтобы не перепутать)
    config --
    """
    photo = []
    # разбиваем по 10 вложений. Медиа отправляется до 10 за раз
    while data["photo"] != []:
        photo.append(data["photo"][:10])
        del data["photo"][:10]

    video = []
    while data["video"] != []:
        video.append(data["video"][:10])
        del data["video"][:10]

    document = []
    while data["document"] != []:
        document.append(data["document"][:10])
        del data["document"][:10]
        
    audio = []
    while data["audio"] != []:
        audio.append(data["audio"][:10])
        del data["audio"][:10]
    
    tasks = []
    if photo:
        # if len(photo[-1]) == 1:
        #     photo[-1].append(types.input_media_photo.InputMediaPhoto(media=config["PHOTO_TO_SEND"]))
        tasks += [asyncio.ensure_future(sending_data(bot, i, message_id, chat_id, mtype="photo")) for i in photo]
    if video:
        tasks += [asyncio.ensure_future(sending_data(bot, i, message_id, chat_id, mtype="video")) for i in video]
    if document:
        tasks += [asyncio.ensure_future(sending_data(bot, i, message_id, chat_id, mtype="document")) for i in document]
    if audio:
        tasks += [asyncio.ensure_future(sending_data(bot, i, message_id, chat_id, mtype="audio")) for i in audio]
    if tasks:
        await asyncio.wait(tasks)
        




# Если вдруг ошибки, что б сообщение точно отправилось
# Может остановить поток
async def sending_data(bot, media, message_id, chat_id, mtype=None):
    while True:
        # try:
        if len(media) != 1:
            await bot.send_media_group(chat_id, media=media, reply_to_message_id=message_id)
        elif mtype == "video":
            await bot.send_video(chat_id, video=media[0].media, reply_to_message_id=message_id)
        elif mtype == "audio":
            await bot.send_audio(chat_id, audio=media[0].media, reply_to_message_id=message_id)
        elif mtype == "photo":
            await bot.send_photo(chat_id, photo=media[0].media, reply_to_message_id=message_id)
        elif mtype == "document":
            await bot.send_document(chat_id, document=media[0].media, reply_to_message_id=message_id)
        break
        # except TelegramForbiddenError as e:
        #     logging.warning(e)
        #     break
        # except AiogramError as e:
        #     logging.warning(e)
        #     await asyncio.sleep(2)
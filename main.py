from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiohttp import ClientSession
from environs import Env
from qqddm import AnimeConverter, InvalidQQDDMApiResponseException, IllegalPictureQQDDMApiResponseException

env = Env()
env.read_env()

telegram_token = env.str('TELEGRAM_TOKEN')

# Proxies are required if you live in a country where the QQ neural network is not available
proxy = env.str('PROXY', None)

bot = Bot(token=telegram_token)
dp = Dispatcher(bot)
anime_converter = AnimeConverter(generate_proxy=proxy)


@dp.message_handler(content_types=types.ContentType.PHOTO)
async def send_image(message: types.Message):
    """
    Получение изображения от пользователя
    """
    await message.answer_chat_action('upload_photo')
    # Берем последнее (самое большое) фото
    photo = message.photo[-1]
    photo_id = photo.file_id
    # Получаем информацию о файле из API
    file_info = await bot.get_file(photo_id)
    file_path = file_info.file_path
    # Скачиваем файл
    downloaded_file = await bot.download_file(file_path)
    # Получаем байты изображения
    image_bytes = downloaded_file.read()
    try:
        # Получаем результат
        result = anime_converter.convert(picture=image_bytes)
        images = [str(url) for url in result.pictures_urls]
        async with ClientSession() as session:
            async with session.get(images[0]) as response:
                content = await response.read()
        # Отправляем изображение пользователю
        await message.answer_photo(content, caption='Your image is ready')
    except IllegalPictureQQDDMApiResponseException:
        await message.answer(text='The provided image is not allowed, please try another image')
    except InvalidQQDDMApiResponseException as ex:
        await message.answer(text=f'API returned an error: {ex}')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
